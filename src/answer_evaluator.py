def evaluate_answer(answer1, answer2, partner1, partner2):
    """
    Evaluate by comparing answers between partners
    
    Args:
        answer1 (str): First partner's answer (1-4)
        answer2 (str): Second partner's answer (1-4)
        
    Returns:
        tuple: (bool for match status, str for feedback message)
    """
    try:
        choice1 = int(answer1.strip())
        choice2 = int(answer2.strip())
        
        if not (1 <= choice1 <= 4 and 1 <= choice2 <= 4):
            return False, "Invalid answer(s). Please use numbers between 1 and 4."
        
        is_match = choice1 == choice2
        if is_match:
            feedback = "💕 <b>Perfect Match!</b> You both chose the same answer!"
        else:
            feedback = f"💔 <b>Different choices.</b> {partner1} chose {choice1}, {partner2} chose {choice2}."
        
        return is_match, feedback
        
    except ValueError:
        return False, "Please answer with a number between 1 and 4."