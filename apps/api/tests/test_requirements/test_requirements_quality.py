"""Unit and integration tests for AI Requirements Analysis quality, dynamic decomposition, and validation."""
import pytest
from app.ai.extractors.requirements_analyzer import (
    analyze_brief_dynamically,
    clean_metadata_leakage,
    validate_and_sanitize_requirements_data,
)


def test_clean_metadata_leakage():
    """Verify that prompt metadata labels are completely stripped."""
    leaked = "Project: Acme Mobile App Client Brief: We want to develop a shopping app."
    cleaned = clean_metadata_leakage(leaked)
    assert "Project:" not in cleaned
    assert "Client Brief:" not in cleaned
    assert "Acme Mobile App" in cleaned
    assert "shopping app" in cleaned


def test_ecommerce_dynamic_requirements_decomposition():
    """Verify Acme Mobile App / E-commerce brief generates specific, high-quality requirements."""
    brief = (
        "We want to develop a mobile application for Acme that allows customers to browse products, "
        "search and filter items, add products to a shopping cart, and place orders. Users should be able "
        "to register and log in using email and password. The app must support secure online payments "
        "through Stripe or Razorpay and send order confirmation emails after successful purchases. "
        "Customers should be able to view their order history, track delivery status, cancel eligible orders, "
        "and manage their profile and saved addresses. Admin users should be able to add, edit, and delete products, "
        "manage inventory, update order statuses, and view customer orders. The app should display clear error "
        "messages for failed payments, unavailable products, and network errors. Passwords must be stored securely, "
        "payment details must not be stored directly in our database, and user data must be protected. "
        "The application should have a clean, modern, mobile-friendly interface and work on both Android and iOS."
    )
    result = analyze_brief_dynamically(
        brief=brief,
        title="Acme Mobile App - E-commerce & Order Tracking",
        project_name="Acme Mobile App",
        desired_outcome="A working cross-platform shopping app with secure checkout and order tracking.",
        constraints="React Native, Node.js, Express.js, PostgreSQL, Stripe/Razorpay, Firebase Cloud Messaging",
    )

    frs = result["functional_requirements"]
    nfrs = result["non_functional_requirements"]
    questions = result["clarification_questions"]

    # 1. Coverage: multiple distinct domain capabilities
    assert len(frs) >= 5, f"Expected at least 5 FRs, got {len(frs)}"
    titles = [f["title"] for f in frs]

    # 2. No generic placeholder titles
    for title in titles:
        assert title != "Core Feature Implementation"
        assert title != "API Validation and Data Persistence"
        assert title != "Feature Implementation"
        assert len(title) > 5

    # 3. Check domain capabilities present
    assert any("Registration" in t or "Authentication" in t for t in titles)
    assert any("Catalog" in t or "Search" in t for t in titles)
    assert any("Cart" in t for t in titles)
    assert any("Payment" in t or "Checkout" in t for t in titles)
    assert any("Order" in t or "Tracking" in t for t in titles)
    assert any("Admin" in t or "Inventory" in t for t in titles)

    # 4. Check no prompt metadata leakage in descriptions
    for fr in frs:
        desc = fr["description"]
        assert "Project:" not in desc
        assert "Client Brief:" not in desc
        assert "Analysis Title:" not in desc
        assert "Desired Outcome:" not in desc
        assert len(desc) >= 20

        # Check acceptance criteria are Given-When-Then and specific
        criteria = fr["acceptance_criteria"]
        assert len(criteria) >= 2
        for c in criteria:
            assert "Given " in c
            assert "When " in c
            assert "Then " in c
            assert "Given authenticated user, when input is supplied, expected result is returned" not in c
            assert "Given valid payload, when submitted, record is stored" not in c

    # 5. Check dependencies are strictly valid and logical
    for fr in frs:
        curr_idx = int(fr["key"].split("-")[1])
        for dep in fr["dependencies"]:
            dep_idx = int(dep.split("-")[1])
            assert dep_idx < curr_idx, f"Dependency {dep} in {fr['key']} is not strictly earlier"

    # 6. Check measurable NFRs
    assert len(nfrs) >= 3
    nfr_categories = [n["category"] for n in nfrs]
    assert "SECURITY" in nfr_categories
    assert "PERFORMANCE" in nfr_categories

    # 7. Check clarification questions
    assert len(questions) >= 2
    for q in questions:
        assert q["question_key"].startswith("Q-")
        assert len(q["question"]) > 10


def test_non_ecommerce_domain_decomposition():
    """Verify that a completely different domain produces domain-specific requirements without e-commerce bias."""
    clinic_brief = (
        "Develop an automated appointment booking portal for a medical clinic. "
        "Patients can register, browse available doctors by specialty, select open time slots, "
        "and schedule appointments. The system sends SMS appointment reminders. "
        "Doctors have a calendar schedule view to set their availability, block off vacation days, "
        "and review their daily patient appointments. Medical staff can export patient appointment logs."
    )
    result = analyze_brief_dynamically(
        brief=clinic_brief,
        title="Clinic Appointment Scheduling Portal",
        project_name="CareClinic",
    )

    frs = result["functional_requirements"]
    titles = [f["title"] for f in frs]

    # Verify no shopping cart or payment gateway hallucinated when not in brief
    assert not any("Shopping Cart" in t for t in titles)
    assert not any("Payment Processing" in t for t in titles)

    # Verify medical booking capabilities are extracted
    assert any("Booking" in t or "Scheduling" in t or "Appointment" in t for t in titles)
    assert any("Authentication" in t or "Registration" in t for t in titles)


def test_validation_and_sanitization_engine():
    """Verify that corrupt or generic inputs are detected and repaired by the validator."""
    corrupted_data = {
        "overview": {
            "project_objective": "Project: Test System Client Brief: Do something",
        },
        "functional_requirements": [
            {
                "key": "FR-99",  # Non-sequential
                "title": "Core Feature Implementation",  # Generic title
                "description": "Project: Test Client Brief: Persist records transactionally in database and validate inputs.",  # Leaked metadata
                "priority": "INVALID_PRIORITY",
                "acceptance_criteria": [
                    "Given authenticated user, when input is supplied, expected result is returned.",  # Generic criteria
                ],
                "dependencies": ["FR-99", "FR-100"],  # Self-dependency & forward dependency
            },
            {
                "key": "FR-1",
                "title": "API Validation and Data Persistence",  # Generic title
                "description": "",  # Empty description
                "priority": "HIGH",
                "acceptance_criteria": [],
                "dependencies": ["FR-2"],  # Invalid forward dependency
            },
        ],
        "non_functional_requirements": [],  # Missing NFRs
        "clarification_questions": [],
    }

    sanitized = validate_and_sanitize_requirements_data(
        parsed=corrupted_data,
        brief="We want an e-commerce grocery delivery mobile app with search, cart, and Stripe checkout.",
        title="Grocery Delivery App",
        project_name="QuickGrocer",
    )

    clean_frs = sanitized["functional_requirements"]
    assert len(clean_frs) >= 2

    # Check keys are sequential FR-1, FR-2
    assert clean_frs[0]["key"] == "FR-1"
    assert clean_frs[1]["key"] == "FR-2"

    # Check generic titles were replaced
    assert clean_frs[0]["title"] != "Core Feature Implementation"
    assert clean_frs[1]["title"] != "API Validation and Data Persistence"

    # Check metadata leakage was stripped
    assert "Project:" not in clean_frs[0]["description"]
    assert "Client Brief:" not in clean_frs[0]["description"]

    # Check generic criteria were replaced with specific Given-When-Then
    for crit in clean_frs[0]["acceptance_criteria"]:
        assert "expected result is returned" not in crit
        assert "Given " in crit
        assert "When " in crit
        assert "Then " in crit

    # Check self-dependency and forward dependency were stripped
    assert "FR-1" not in clean_frs[0]["dependencies"]
    assert "FR-99" not in clean_frs[0]["dependencies"]
    assert "FR-100" not in clean_frs[0]["dependencies"]
    assert "FR-2" not in clean_frs[0]["dependencies"]

    # Check NFRs were restored
    assert len(sanitized["non_functional_requirements"]) >= 3
    assert len(sanitized["clarification_questions"]) >= 1

