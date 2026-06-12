from nis.models.user_profile import UserProfile
from nis.models.match_preference import MatchPreference
from nis.models.candidate_profile import CandidateProfile

class MatchScoreEngine:
    """
    Calculates a private internal score from 0 to 100 for candidates who already passed hard blocks and dealbreaker checks.
    This score is only for internal ranking and must not be shown to the frontend.
    """
    
    MIN_ACCEPTABLE_SCORE = 60

    @staticmethod
    def calculate_score(seeker_profile: UserProfile, seeker_prefs: MatchPreference, candidate: CandidateProfile, candidate_prefs: MatchPreference) -> dict:
        score = 0
        cand_prof = candidate.profile
        
        # 1. Religious Alignment (Max 20 points)
        rel_score = 20
        if seeker_prefs.preferred_tradition and cand_prof.tradition != seeker_prefs.preferred_tradition:
            rel_score -= 10
        if seeker_prefs.preferred_islamic_environment and cand_prof.islamic_environment_preference != seeker_prefs.preferred_islamic_environment:
            rel_score -= 5
        if seeker_prefs.religious_practice_importance == "HIGH" and cand_prof.religious_practice_level != "HIGH":
            rel_score -= 5
        score += max(0, rel_score)
        
        # 2. Preference Alignment (Max 25 points)
        # Location, Education, Age, Height
        pref_score = 25
        if seeker_prefs.preferred_locations and cand_prof.location not in seeker_prefs.preferred_locations:
            pref_score -= 5
        if seeker_prefs.preferred_education_levels and cand_prof.education_level not in seeker_prefs.preferred_education_levels:
            pref_score -= 5
        if cand_prof.age < seeker_prefs.preferred_min_age or cand_prof.age > seeker_prefs.preferred_max_age:
            pref_score -= 5
        if cand_prof.height_cm and seeker_prefs.preferred_min_height_cm and seeker_prefs.preferred_max_height_cm:
            if cand_prof.height_cm < seeker_prefs.preferred_min_height_cm or cand_prof.height_cm > seeker_prefs.preferred_max_height_cm:
                pref_score -= 5
        if seeker_prefs.preferred_occupations and cand_prof.occupation not in seeker_prefs.preferred_occupations:
            pref_score -= 5
        score += max(0, pref_score)
        
        # 3. Family/Wali Alignment (Max 15 points)
        fam_score = 15
        if seeker_prefs.family_involvement_preference and cand_prof.family_involvement != seeker_prefs.family_involvement_preference:
            fam_score -= 5
        if seeker_prefs.family_boundaries_importance and cand_prof.boundary_strength != seeker_prefs.family_boundaries_importance:
            fam_score -= 5
        # Unknown values reduce confidence slightly
        if cand_prof.family_pressure_level == "UNKNOWN":
            fam_score -= 2
        score += max(0, fam_score)
        
        # 4. Communication Compatibility (Max 15 points)
        comm_score = 15
        if seeker_prefs.communication_preference and cand_prof.communication_style != seeker_prefs.communication_preference:
            comm_score -= 5
        if seeker_prefs.conflict_style_preference and cand_prof.conflict_aggression_level != "UNKNOWN":
            if cand_prof.conflict_aggression_level != seeker_prefs.conflict_style_preference: # simplified check
                comm_score -= 5
        if seeker_prefs.preferred_repair_style and cand_prof.repair_style != seeker_prefs.preferred_repair_style:
            comm_score -= 5
        score += max(0, comm_score)
        
        # 5. Psychology/Emotional Safety (Max 15 points)
        psych_score = 15
        if cand_prof.emotional_steadiness != "STEADY":
            psych_score -= 5
        if cand_prof.anger_level != "LOW":
            psych_score -= 5
        if cand_prof.attachment_style not in ["SECURE", "UNKNOWN"]:
            psych_score -= 5
        score += max(0, psych_score)
        
        # 6. Lifestyle/Work/Marriage Readiness (Max 10 points)
        life_score = 10
        if cand_prof.marriage_readiness != "READY":
            life_score -= 4
        if seeker_prefs.preferred_lifestyle_pattern and cand_prof.lifestyle_pattern != seeker_prefs.preferred_lifestyle_pattern:
            life_score -= 3
        if seeker_prefs.preferred_work_outlook and cand_prof.work_outlook not in seeker_prefs.preferred_work_outlook:
            life_score -= 3
        score += max(0, life_score)
        
        # Ensure score is bound between 0 and 100
        final_score = max(0, min(100, score))
        
        classification = MatchScoreEngine._classify_score(final_score)
        
        return {
            "internal_score": final_score,
            "classification": classification,
            "is_acceptable": final_score >= MatchScoreEngine.MIN_ACCEPTABLE_SCORE
        }

    @staticmethod
    def _classify_score(score: int) -> str:
        if score >= 90:
            return "VERY_STRONG_ALIGNMENT"
        elif score >= 80:
            return "STRONG_ALIGNMENT"
        elif score >= 70:
            return "GOOD_ALIGNMENT"
        elif score >= 60:
            return "ACCEPTABLE_ALIGNMENT"
        else:
            return "LOW_ALIGNMENT"
