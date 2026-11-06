from typing import Dict, Any
import business_config

def get_template_catalog() -> Dict[str, str]:
    """Returns the catalog of available follow-up message templates."""
    return {
        "acknowledgement": "1. Initial Enquiry Acknowledgement",
        "budget_clarification": "2. Budget Clarification & Scope Alignment",
        "requirements_clarification": "3. Project Requirements Clarification",
        "site_visit_invitation": "4. Complimentary Site Visit Invitation",
        "portfolio_sharing": "5. Curated Design Portfolio & Moodboard",
        "no_response": "6. Polite Follow-up (No Response)",
        "consultation_scheduling": f"7. {business_config.OFFICE_NAME.title()} Consultation Scheduling"
    }

def generate_personalized_message(
    template_type: str,
    lead: Dict[str, Any],
    designer_name: str = "SHA Design Consultant"
) -> str:
    """
    Generates a personalised follow-up message draft using available customer details.
    Drafts only; does not send real external communications.
    """
    name = lead.get("customer_name", "Valued Client")
    city = lead.get("city", "your city")
    p_type = lead.get("project_type", "home interior")
    budget = lead.get("budget_range", "your budget")
    timeline = lead.get("project_timeline", "your timeline")
    scope = lead.get("scope_of_work", "interior design")
    
    if template_type == "acknowledgement":
        return (
            f"Hello {name}, thank you for reaching out to SHA Interface Interiors! "
            f"We have received your enquiry for your {p_type} project in {city}. "
            f"Our design team is reviewing your requirements for {scope}. "
            f"When would be a convenient time for a brief 10-minute discovery call to explore initial concepts?"
        )
        
    elif template_type == "budget_clarification":
        return (
            f"Dear {name}, following up on your {p_type} project in {city}. "
            f"To ensure our 3D design concepts align with your expectations around the {budget} range, "
            f"could you share if this covers complete turnkey finishes or modular woodwork specifically? "
            f"We want to maximize value within your investment preferences."
        )
        
    elif template_type == "requirements_clarification":
        return (
            f"Hi {name}, we are preparing preliminary space-planning ideas for your {p_type} in {city}. "
            f"Given your preference for {scope}, do you have specific architectural floor plans or builder handovers "
            f"you could share with us on WhatsApp or email? This will help us draft accurate 3D layout options."
        )
        
    elif template_type == "site_visit_invitation":
        return (
            f"Hello {name}, our senior design consultant will be visiting ongoing project sites in {city} this week. "
            f"Since your property status is '{lead.get('property_status', 'Ready')}', we would love to offer a "
            f"complimentary on-site measurement & spatial audit for your {p_type}. "
            f"Would Saturday or Sunday work better for you?"
        )
        
    elif template_type == "portfolio_sharing":
        return (
            f"Hello {name}, here are recently completed {p_type} interior projects by SHA Interface Interiors in {city}. "
            f"Our clients loved the combination of modern aesthetics and smart space-saving modular woodwork. "
            f"Take a look at our lookbook here: https://shainteriors.example.com/lookbook/{city.lower()} "
            f"Let us know which design style resonates most with you!"
        )
        
    elif template_type == "no_response":
        return (
            f"Hi {name}, we tried connecting earlier regarding your {p_type} inquiry in {city}. "
            f"We know you are busy planning your move ({timeline}). Whenever you are ready, "
            f"feel free to reply here or let us know if you'd like us to pause updates. Have a wonderful week!"
        )
        
    elif template_type == "consultation_scheduling":
        return (
            f"Dear {name}, we would be delighted to arrange a meeting at our {business_config.OFFICE_NAME} or schedule a convenient phone call "
            f"to discuss your {p_type} vision in {city}. Our general office hours are {business_config.OFFICE_HOURS_START} to {business_config.OFFICE_HOURS_END} {business_config.TIMEZONE}, Monday through Sunday, "
            f"with customer consultation appointments available between {business_config.APPOINTMENT_HOURS_START} and {business_config.APPOINTMENT_HOURS_END} {business_config.TIMEZONE}.\n\n"
            f"You can view our location on Google Maps here: {business_config.OFFICE_MAPS_LINK} .\n\n"
            f"Please let us know your preferred date and time between {business_config.APPOINTMENT_HOURS_START} and {business_config.APPOINTMENT_HOURS_END}, and our team will assist you with confirming the appointment."
        )
        
    else:
        # Default warm inquiry follow-up
        return (
            f"Hello {name}, thank you for your interest in {business_config.BUSINESS_NAME}. "
            f"We would love to arrange a meeting at our {business_config.OFFICE_NAME} or schedule a phone call to understand your {p_type} requirements "
            f"and discuss suitable interior options within your {budget} budget in {city}. "
            f"Customer consultation appointments at our {business_config.OFFICE_NAME} are available between {business_config.APPOINTMENT_HOURS_START} and {business_config.APPOINTMENT_HOURS_END} {business_config.TIMEZONE}, Monday through Sunday."
        )
