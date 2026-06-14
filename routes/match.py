from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Preferences, ConsideredSet, CandidateInteraction, Conversation, PsychologicalProfile
from security import get_current_user
import uuid

from nis.services.nis_matchmaking_service import NISMatchmakingService
from nis.adapters.db_to_nis_mapper import (
    map_db_user_to_user_profile, 
    map_db_candidate_to_candidate_profile, 
    map_db_preference_to_match_preference
)
from nis.models.candidate_pool_context import CandidatePoolContext
from nis.models.mutual_interest_state import MutualInterestState
from nis.engines.mutual_interest_gate_engine import evaluate_mutual_interest_gate
import schemas

router = APIRouter(prefix="/sakinah", tags=["Matchmaking"])

@router.post("/match-preference")
def update_preferences(req: schemas.MatchPreferenceRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.preferences:
        current_user.preferences = Preferences(user_id=current_user.id)
    
    # Basic Preferences
    current_user.preferences.preferred_age_min = int(req.minAge) if req.minAge else None
    current_user.preferences.preferred_age_max = int(req.maxAge) if req.maxAge else None
    current_user.preferences.preferred_city = req.locationPref
    current_user.preferences.location_flexibility = req.locationFlexibility
    current_user.preferences.marital_status = req.maritalStatus
    current_user.preferences.preferred_education = req.educationPref
    current_user.preferences.work_outlook = req.workOutlook
    current_user.preferences.work_after_marriage = req.workAfterMarriage
    
    # Religious & Family
    current_user.preferences.tradition_pref = req.traditionPref
    current_user.preferences.tradition_strictness = req.traditionStrictness
    current_user.preferences.preferred_religious_level = req.religiousPracticePref
    current_user.preferences.islamic_env_pref = req.islamicEnvPref
    current_user.preferences.learning_pref = req.learningPref
    current_user.preferences.reminder_style = req.reminderStyle
    current_user.preferences.family_involvement = req.familyInvolvement
    current_user.preferences.marriage_timeline = req.marriageTimeline
    
    # Dealbreakers
    current_user.preferences.dealbreakers_text = req.dealbreakersText
    current_user.preferences.strict_age = req.strictAge
    current_user.preferences.strict_location = req.strictLocation
    current_user.preferences.strict_tradition = req.strictTradition
    current_user.preferences.strict_marital = req.strictMarital
    current_user.preferences.no_match_confirmed = req.noMatchConfirmed

    # Psychological Profile
    if not current_user.psychological_profile:
        current_user.psychological_profile = PsychologicalProfile(user_id=current_user.id)
        
    current_user.psychological_profile.communication_style = req.communicationStyle
    current_user.psychological_profile.conflict_resolution = req.repairStyle
    current_user.psychological_profile.anger_level = req.angerLevel
    current_user.psychological_profile.boundary_strength = req.boundaryStrength
    current_user.psychological_profile.emotional_steadiness = req.emotionalSteadiness
    current_user.psychological_profile.financial_responsibility = req.financialResp
    current_user.psychological_profile.lifestyle_pattern = req.lifestyle
    current_user.psychological_profile.disagreement_response = req.disagreementResponse
    current_user.psychological_profile.family_pressure_response = req.familyPressureResponse
    current_user.psychological_profile.accountability_response = req.accountabilityResponse
    current_user.psychological_profile.personal_space_response = req.personalSpaceResponse
    current_user.psychological_profile.financial_expectations = req.financialDecisionResponse
    
    db.add(current_user)
    db.commit()
    return {"message": "Preferences saved successfully"}

@router.post("/matches/generate")
def generate_matches(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Fetch current user (Already verified by JWT!)
    seeker = current_user
    user_id = seeker.id
        
    # 2. Build NIS Dictionaries
    psy_prof = seeker.psychological_profile
    db_pref = seeker.preferences
    
    user_dict = {
        "user_id": seeker.id, "name": seeker.full_name, "age": seeker.age, "gender": seeker.gender,
        "location": seeker.city, "education_level": seeker.education, "occupation": seeker.occupation,
        "is_verified": seeker.kyc_status == "verified", "is_banned": seeker.is_banned,
        "safety_status": seeker.safety_status, "has_required_data": True,
        "marital_status": db_pref.marital_status if db_pref else "NEVER_MARRIED",
        "work_outlook": db_pref.work_outlook if db_pref else None,
        "islamic_environment_preference": db_pref.islamic_env_pref if db_pref else None,
        "religious_practice_level": db_pref.preferred_religious_level if db_pref else None,
        "communication_style": psy_prof.communication_style if psy_prof else "Calm", 
        "tradition": db_pref.tradition_pref if db_pref else "Sunni",
        "anger_level": psy_prof.anger_level if psy_prof else None,
        "repair_style": psy_prof.conflict_resolution if psy_prof else None,
        "boundary_strength": psy_prof.boundary_strength if psy_prof else None,
        "emotional_steadiness": psy_prof.emotional_steadiness if psy_prof else None,
        "financial_responsibility": psy_prof.financial_responsibility if psy_prof else None,
        "lifestyle_pattern": psy_prof.lifestyle_pattern if psy_prof else None,
        "_raw_psychological_profile": psy_prof
    }
    
    pref_dict = {}
    if db_pref:
        pref_dict = {
            "preferred_min_age": db_pref.preferred_age_min, "preferred_max_age": db_pref.preferred_age_max,
            "preferred_locations": [db_pref.preferred_city] if db_pref.preferred_city else [],
            "preferred_education_levels": [db_pref.preferred_education] if db_pref.preferred_education else [],
            "age_is_strict": db_pref.strict_age,
            "location_is_strict": db_pref.strict_location,
            "tradition_is_strict": db_pref.strict_tradition,
            "marital_status_is_strict": db_pref.strict_marital,
            "preferred_marital_statuses": [db_pref.marital_status] if db_pref.marital_status else [],
            "preferred_tradition": db_pref.tradition_pref,
            "preferred_islamic_environment": db_pref.islamic_env_pref,
            "preferred_work_outlook": [db_pref.work_outlook] if db_pref.work_outlook else [],
            "family_involvement_preference": db_pref.family_involvement,
            "communication_preference": psy_prof.communication_style if psy_prof else None,
            "custom_dealbreakers": [db_pref.dealbreakers_text] if db_pref.dealbreakers_text else [],
            "confirmed_no_match_over_wrong_match": db_pref.no_match_confirmed
        }
        
    # 3. Fetch Candidate Pool
    other_users = db.query(User).filter(
        User.id != user_id, 
        User.gender != seeker.gender,
        User.is_banned == False,
        User.kyc_status == "verified",
        User.safety_status == "CLEAR"
    ).all()
    
    candidate_dicts = []
    for u in other_users:
        c_psy = u.psychological_profile
        c_pref = u.preferences
        candidate_dicts.append({
            "candidate_id": u.id,
            "profile": {
                "user_id": u.id, "name": u.full_name, "age": u.age, "gender": u.gender,
                "location": u.city, "education_level": u.education, "occupation": u.occupation,
                "is_verified": True, "is_banned": False, "safety_status": "CLEAR", "has_required_data": True,
                "marital_status": c_pref.marital_status if c_pref else "NEVER_MARRIED",
                "work_outlook": c_pref.work_outlook if c_pref else None,
                "islamic_environment_preference": c_pref.islamic_env_pref if c_pref else None,
                "religious_practice_level": c_pref.preferred_religious_level if c_pref else None,
                "communication_style": c_psy.communication_style if c_psy else "Calm", 
                "tradition": c_pref.tradition_pref if c_pref else "Sunni", 
                "marriage_readiness": c_psy.marriage_readiness if c_psy else "READY",
                "anger_level": c_psy.anger_level if c_psy else None,
                "repair_style": c_psy.conflict_resolution if c_psy else None,
                "emotional_steadiness": c_psy.emotional_steadiness if c_psy else None,
                "financial_responsibility": c_psy.financial_responsibility if c_psy else None,
                "lifestyle_pattern": c_psy.lifestyle_pattern if c_psy else None,
                "_raw_psychological_profile": c_psy
            }
        })

    # 4. Map Dictionaries to NIS Objects
    nis_user = map_db_user_to_user_profile(user_dict)
    nis_pref = map_db_preference_to_match_preference(pref_dict)
    nis_candidates = [map_db_candidate_to_candidate_profile(c) for c in candidate_dicts]

    # 5. Build CandidatePoolContext
    active_convos = db.query(Conversation).filter(
        (Conversation.seeker_a_id == user_id) | (Conversation.seeker_b_id == user_id),
        Conversation.status == "ACTIVE"
    ).all()
    active_convos_count = len(active_convos)
    
    active_convo_candidate_ids = []
    for c in active_convos:
        active_convo_candidate_ids.append(c.seeker_b_id if c.seeker_a_id == user_id else c.seeker_a_id)

    interactions = db.query(CandidateInteraction).filter(CandidateInteraction.seeker_id == user_id).all()
    shown_ids = [i.candidate_id for i in interactions if i.status == "SHOWN"]
    passed_ids = [i.candidate_id for i in interactions if i.status == "PASS"]
    
    pool_context = CandidatePoolContext(
        seeker_id=user_id,
        active_conversations_count=active_convos_count,
        max_active_conversations=2,
        shown_candidate_ids=shown_ids,
        passed_candidate_ids=passed_ids,
        blocked_candidate_ids=[],
        active_conversation_candidate_ids=active_convo_candidate_ids,
        max_considered_candidates=3
    )

    # 6. Execute NIS
    result = NISMatchmakingService.generate_considered_few(
        current_user=nis_user,
        match_preference=nis_pref,
        candidates=nis_candidates,
        pool_context=pool_context
    )
    
    # 7. Store Result safely
    if result.get("status") == "HAS_CONSIDERED_CANDIDATES":
        c_set_id = str(uuid.uuid4())
        candidate_ids = [c["candidate_id"] for c in result.get("candidates", [])]
        
        c_set = ConsideredSet(
            considered_set_id=c_set_id, seeker_id=user_id,
            candidate_ids=candidate_ids, nis_status=result.get("status")
        )
        db.add(c_set)
        
        for cid in candidate_ids:
            interaction = CandidateInteraction(
                seeker_id=user_id, candidate_id=cid, 
                status="SHOWN", considered_set_id=c_set_id
            )
            db.add(interaction)
        db.commit()

        # Re-attach profile data for the frontend
        for c in result.get("candidates", []):
            cid = c["candidate_id"]
            original = next((cd for cd in candidate_dicts if cd["candidate_id"] == cid), None)
            if original:
                c["profile"] = original["profile"]

    return result

@router.post("/candidates/{candidate_id}/pass")
def pass_candidate(candidate_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.id
    interaction = CandidateInteraction(
        seeker_id=user_id, candidate_id=candidate_id, status="PASS"
    )
    db.add(interaction)
    db.commit()
    return {"status": "success", "message": "Candidate passed silently."}

@router.post("/candidates/{candidate_id}/interest")
def express_interest(candidate_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.id
    interaction = CandidateInteraction(
        seeker_id=user_id, candidate_id=candidate_id, status="INTEREST"
    )
    db.add(interaction)
    db.commit()
    
    # Auto-evaluate mutual interest
    candidate_interest = db.query(CandidateInteraction).filter_by(seeker_id=candidate_id, candidate_id=user_id, status="INTEREST").first()
    if candidate_interest:
        existing = db.query(Conversation).filter(
            ((Conversation.seeker_a_id == user_id) & (Conversation.seeker_b_id == candidate_id)) |
            ((Conversation.seeker_a_id == candidate_id) & (Conversation.seeker_b_id == user_id))
        ).first()
        if not existing:
            import uuid
            new_convo = Conversation(
                conversation_id=str(uuid.uuid4()), seeker_a_id=user_id, seeker_b_id=candidate_id
            )
            db.add(new_convo)
            db.commit()
        return {"status": "mutual_interest", "message": "Mutual interest confirmed!"}
            
    return {"status": "success", "message": "Interest recorded privately."}

@router.post("/mutual-interest/evaluate")
def evaluate_mutual_interest(candidate_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.id
    seeker_interest = db.query(CandidateInteraction).filter_by(seeker_id=user_id, candidate_id=candidate_id, status="INTEREST").first()
    candidate_interest = db.query(CandidateInteraction).filter_by(seeker_id=candidate_id, candidate_id=user_id, status="INTEREST").first()
    seeker_pass = db.query(CandidateInteraction).filter_by(seeker_id=user_id, candidate_id=candidate_id, status="PASS").first()
    candidate_pass = db.query(CandidateInteraction).filter_by(seeker_id=candidate_id, candidate_id=user_id, status="PASS").first()
    
    state = MutualInterestState(
        seeker_id=user_id, candidate_id=candidate_id,
        seeker_interested=bool(seeker_interest), candidate_interested=bool(candidate_interest),
        seeker_passed=bool(seeker_pass), candidate_passed=bool(candidate_pass)
    )
    
    gate_result = evaluate_mutual_interest_gate(state)
    
    if gate_result.get("status") == "MUTUAL_INTEREST_CONFIRMED":
        existing = db.query(Conversation).filter(
            ((Conversation.seeker_a_id == user_id) & (Conversation.seeker_b_id == candidate_id)) |
            ((Conversation.seeker_a_id == candidate_id) & (Conversation.seeker_b_id == user_id))
        ).first()
        if not existing:
            new_convo = Conversation(
                conversation_id=str(uuid.uuid4()), seeker_a_id=user_id, seeker_b_id=candidate_id
            )
            db.add(new_convo)
            db.commit()
            
    return {"status": gate_result.get("status")}
