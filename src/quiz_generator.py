import pandas as pd
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage
)
from llama_index.core.ingestion import IngestionCache, IngestionPipeline
from llama_index.core.text_splitter import TokenTextSplitter
from llama_index.core.extractors import SummaryExtractor
from llama_index.program.openai import OpenAIPydanticProgram
from llama_index.program.evaporate.df import DFRowsProgram
from llama_index.embeddings.openai import OpenAIEmbedding

from global_settings import (
    OPENAI_API_KEY,
    OPENAI_EMBED,
    OPENAI_LLM,
    STORAGE_PATH,
    INGESTION_FILE,
    INDEX_PATH,
    QUIZ_FILE,
)

import logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
Settings.llm = OpenAI(
    api_key=OPENAI_API_KEY,
    model=OPENAI_LLM,
    temperature=0.9
)
Settings.embed_model = OpenAIEmbedding(
    api_key=OPENAI_API_KEY,
    model=OPENAI_EMBED
)

from llama_index.core.prompts import RichPromptTemplate
template = RichPromptTemplate(
    """
    Goal: {{goal_str}}
    ---
    Cotext: {{context_str}}
    ---
    Output Strucutre {{output_str}}
    ---
    Avoidance: {{avoidance_str}}
    """
)



def ingestion():
    """
    * Purpose: Prepares the context for generating respones
    * Process:
        1. Reads all files from storage directory as Documents
        2. Chunks the raw Documents into Nodes
        3. Extracts metadata
        4. Caches those Nodes for further uses (if there already in cache, just use it, no need to re-process)
    """

    # Read all readable documents available in STORAGE_PATH
    documents = SimpleDirectoryReader(
        STORAGE_PATH,
        filename_as_id=True
    ).load_data()

    # Checks if there's already cached pipeline data to use
    try:
        cached_hashed = IngestionCache.from_persist_path(INGESTION_FILE)
        logger.info(f"Cache file found, Running with ingested data")
    except:
        cached_hashed = ""
        logger.info("No cache. Running without")

    # Run the pipeline
    pipeline = IngestionPipeline(
        transformations=[
            TokenTextSplitter(chunk_size=1024, chunk_overlap=20),
            SummaryExtractor(summaries=["self"]),
            Settings.embed_model # Using embedding model to prepare format for vector indexing
        ],
        cache=cached_hashed # Uses cached data if available to skip reprocessing unchanged documents.
    )

    nodes = pipeline.run(documents=documents)
    pipeline.cache.persist(INGESTION_FILE)

    return nodes


def indexing(nodes):
    """
    This function indexes documents (nodes) for structure, retrieve, and update data efficiently.
    """
        
    try:
        storage_context = StorageContext.from_defaults(persist_dir=INDEX_PATH)
        vector_index = load_index_from_storage(storage_context, index_id="vector")
        logger.info("All indices loaded from storage")
    except Exception as e:
        logger.error(f"Error occured while loading indices: {e}")
        storage_context = StorageContext.from_defaults()
        vector_index = VectorStoreIndex(nodes, storage_context=storage_context)
        vector_index.set_index_id("vector")
        storage_context.persist(persist_dir=INDEX_PATH)
        logger.info("New indices were created and persisted")

    return vector_index


def main(nodes):
    """
    """

    # Set up a DataFrame to structure the quiz questions
    df = pd.DataFrame({
        "Question_no": pd.Series(dtype="int"),
        "Question_text": pd.Series(dtype="str"),
        "Option1": pd.Series(dtype="str"),
        "Option2": pd.Series(dtype="str"),
        "Option3": pd.Series(dtype="str"),
        "Option4": pd.Series(dtype="str")
    })

    vector_index = indexing(nodes)

    # Load existing question if file exists, othereise use empty dataframe
    try:
        existing_df = pd.read_csv(QUIZ_FILE)
        start_question_no = len(existing_df) + 1
        existing_questions = existing_df["Question_text"].tolist()
    except FileNotFoundError:
        existing_df = pd.DataFrame()
        start_question_no = 1

    avoiding_questions = " ".join(set(existing_questions))
    prompt_str = template.format(
        goal_str="Need you to create only 1 single quiz question with 4 answer options for each quiz that should be creativity and relies heavily on our provided documents.",
        context_str="I and my girlfriend will use these questions as content for our night game and choose the answer to test how well we understand each other and the relationship.",
        output_str="There must 5 outcome information: 1 question and 4 answer options for each question. The question should not contain any special character.",
        avoidance_str=f"Please avoid to create a same question from this list {avoiding_questions}"
    )

    # Define the query engine and craft a prmpt to generate uniqe quiz
    query_engine = vector_index.as_query_engine()
    response = query_engine.query(prompt_str)
    logger.info(f"Response: {response}")

    # Initialize the DataFrame extractor
    df_rows_program = DFRowsProgram.from_defaults(
        pydantic_program_cls=OpenAIPydanticProgram,
        df=df
    )
    result_obj = df_rows_program(input_str=response)
    new_question_df = result_obj.to_df(existing_df=df)

    
    # Add sequenctial question numbers to new questions
    new_question_df["Question_no"] = range(start_question_no, start_question_no + len(new_question_df))

    # Combine with exisitng questions if any
    if start_question_no > 1:
        combined_df = pd.concat(
            [existing_df, new_question_df],
            ignore_index=True
        )
    else:
        combined_df = new_question_df
    combined_df.to_csv(QUIZ_FILE, index=False)


if __name__ == "__main__":
    nodes = ingestion()

    for i in range(0, 2):
        logger.info(f"Iterate #{i}: \n")
        main(nodes)