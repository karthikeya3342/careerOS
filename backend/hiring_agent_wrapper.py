import os
import sys
import contextlib

@contextlib.contextmanager
def sys_path_and_cwd_context():
    """Temporarily sets current working directory and sys.path for hiring-agent execution."""
    old_cwd = os.getcwd()
    hiring_agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "hiring-agent"))
    
    # Change CWD to hiring-agent
    os.chdir(hiring_agent_dir)
    sys.path.insert(0, hiring_agent_dir)
    try:
        yield
    finally:
        os.chdir(old_cwd)
        if sys.path[0] == hiring_agent_dir:
            sys.path.pop(0)

def evaluate_candidate_resume(pdf_path: str, github_url: str = None) -> dict:
    """Runs the hiring-agent evaluation pipeline on a compiled PDF resume."""
    pdf_path = os.path.abspath(pdf_path)
    with sys_path_and_cwd_context():
        # Lazy import of score and models from hiring-agent
        import score
        from models import JSONResume
        
        # Ensure output cache folder exists inside hiring-agent directory
        os.makedirs("cache", exist_ok=True)
        
        # Run main scoring pipeline
        # score.main takes the pdf_path (relative or absolute)
        # It handles extracting and evaluating.
        # We temporarily set GITHUB_TOKEN or other keys if available.
        # But we already fetched GitHub data during onboarding, so we can mock or pass it.
        # If github_url is passed, score.main will automatically look up the profiles or we can override.
        evaluation = score.main(pdf_path)
        
        if not evaluation:
            return {"score": 0, "breakdown": "Failed to parse resume PDF"}
            
        # Calculate overall score matching score.py printing logic
        total_score = 0
        max_score = 0
        
        if hasattr(evaluation, "scores") and evaluation.scores:
            for category_name, category_data in evaluation.scores.model_dump().items():
                total_score += min(category_data["score"], category_data["max"])
                max_score += category_data["max"]
                
        if hasattr(evaluation, "bonus_points") and evaluation.bonus_points:
            total_score += evaluation.bonus_points.total
        if hasattr(evaluation, "deductions") and evaluation.deductions:
            total_score -= evaluation.deductions.total
            
        max_possible_score = max_score + 20
        if total_score > max_possible_score:
            total_score = max_possible_score
            
        return {
            "total_score": round(total_score, 1),
            "max_score": max_score,
            "strengths": getattr(evaluation, "key_strengths", []),
            "improvements": getattr(evaluation, "areas_for_improvement", []),
            "bonus": getattr(evaluation.bonus_points, "total", 0) if hasattr(evaluation, "bonus_points") else 0,
            "deductions": getattr(evaluation.deductions, "total", 0) if hasattr(evaluation, "deductions") else 0,
            "deductions_reasons": getattr(evaluation.deductions, "reasons", "") if hasattr(evaluation, "deductions") else "",
            "raw_evaluation": evaluation.model_dump() if hasattr(evaluation, "model_dump") else str(evaluation)
        }

def evaluate_candidate_profile(profile_text: str) -> dict:
    """Runs the hiring-agent ResumeEvaluator directly on candidate profile text (no PDF needed)."""
    with sys_path_and_cwd_context():
        from evaluator import ResumeEvaluator
        evaluator = ResumeEvaluator()
        evaluation = evaluator.evaluate_resume(profile_text)
        
        if not evaluation:
            return {"total_score": 0, "improvements": [], "deductions_reasons": "Could not score profile."}
            
        total_score = 0
        max_score = 0
        
        if hasattr(evaluation, "scores") and evaluation.scores:
            for category_name, category_data in evaluation.scores.model_dump().items():
                total_score += min(category_data["score"], category_data["max"])
                max_score += category_data["max"]
                
        if hasattr(evaluation, "bonus_points") and evaluation.bonus_points:
            total_score += evaluation.bonus_points.total
        if hasattr(evaluation, "deductions") and evaluation.deductions:
            total_score -= evaluation.deductions.total
            
        max_possible_score = max_score + 20
        if total_score > max_possible_score:
            total_score = max_possible_score
            
        return {
            "total_score": round(total_score, 1),
            "max_score": max_score,
            "strengths": getattr(evaluation, "key_strengths", []),
            "improvements": getattr(evaluation, "areas_for_improvement", []),
            "bonus": getattr(evaluation.bonus_points, "total", 0) if hasattr(evaluation, "bonus_points") else 0,
            "deductions": getattr(evaluation.deductions, "total", 0) if hasattr(evaluation, "deductions") else 0,
            "deductions_reasons": getattr(evaluation.deductions, "reasons", "") if hasattr(evaluation, "deductions") else "",
            "raw_evaluation": evaluation.model_dump() if hasattr(evaluation, "model_dump") else str(evaluation)
        }
