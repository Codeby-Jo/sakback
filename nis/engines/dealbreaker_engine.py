from nis.models.user_profile import UserProfile
from nis.models.match_preference import MatchPreference
from nis.models.candidate_profile import CandidateProfile

class DealbreakerEngine:
    """
    Evaluates dealbreakers between seeker and candidate.
    Returns PASS or BLOCKED_BY_SEEKER_DEALBREAKER or BLOCKED_BY_CANDIDATE_DEALBREAKER.
    """

    @staticmethod
    def evaluate(seeker_profile: UserProfile, seeker_prefs: MatchPreference, candidate: CandidateProfile, candidate_prefs: MatchPreference) -> dict:
        
        candidate_traits = DealbreakerEngine._extract_traits(candidate.profile)
        # Include any externally provided traits
        if candidate.known_dealbreaker_traits:
            candidate_traits.extend(candidate.known_dealbreaker_traits)

        seeker_traits = DealbreakerEngine._extract_traits(seeker_profile)

        # 1. Seeker dealbreakers against candidate
        if seeker_prefs and seeker_prefs.dealbreakers:
            for db in seeker_prefs.dealbreakers:
                if db in candidate_traits:
                    return {
                        "status": "BLOCKED_BY_SEEKER_DEALBREAKER",
                        "private_reason": f"Candidate has seeker dealbreaker: {db}"
                    }

        # 2. Candidate dealbreakers against seeker
        if candidate_prefs and candidate_prefs.dealbreakers:
            for db in candidate_prefs.dealbreakers:
                if db in seeker_traits:
                    return {
                        "status": "BLOCKED_BY_CANDIDATE_DEALBREAKER",
                        "private_reason": f"Seeker has candidate dealbreaker: {db}"
                    }

        return {
            "status": "PASS",
            "private_reason": None
        }

    @staticmethod
    def _extract_traits(profile: UserProfile) -> list[str]:
        traits = []
        if profile.marriage_readiness == "NOT_READY":
            traits.append("NOT_READY_FOR_MARRIAGE")
        
        # Add basic traits that could be dealbreakers
        traits.append(f"OCCUPATION_{str(profile.occupation).upper().replace(' ', '_')}")
        traits.append(f"EDUCATION_{str(profile.education_level).upper().replace(' ', '_')}")
        traits.append(f"LOCATION_{str(profile.location).upper().replace(' ', '_')}")
        
        if profile.marital_status:
            traits.append(f"STATUS_{str(profile.marital_status).upper().replace(' ', '_')}")
            
        return traits
