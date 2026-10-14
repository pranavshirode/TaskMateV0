"""Unit and integration tests for AI Requirements Analysis quality, dynamic decomposition, and validation."""

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
    assert any("Sign-in" in t or "Accounts" in t for t in titles)
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

    # 6. NFRs reflect what the brief asks for (secure storage; Android and iOS) and nothing it doesn't
    nfr_categories = [n["category"] for n in nfrs]
    assert "SECURITY" in nfr_categories
    assert "COMPATIBILITY" in nfr_categories
    assert "PERFORMANCE" not in nfr_categories  # the brief never mentions speed
    assert all(n["source"] in ("CLIENT_STATED", "AI_SUGGESTED") for n in nfrs)
    assert all(f["source"] == "CLIENT_STATED" for f in frs)

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
    assert any("Sign-in" in t or "Accounts" in t for t in titles)


def test_validation_and_sanitization_engine():
    """Corrupt AI output is cleaned and validated, but never padded with invented content."""
    corrupted_data = {
        "overview": {"project_objective": "Project: Test System Client Brief: Do something"},
        "functional_requirements": [
            {
                "key": "FR-99",  # Non-sequential
                "title": "Grocery Search",
                "description": "Project: Test Client Brief: Customers search groceries by name.",  # Leaked metadata
                "priority": "INVALID_PRIORITY",
                "acceptance_criteria": [
                    "Given authenticated user, when input is supplied, expected result is returned.",  # Generic
                    "given a product name, when searching, then matching products are listed",
                ],
                "dependencies": ["FR-99", "FR-100"],  # Self & forward dependency
                "source": "client_stated",
            },
            {
                "key": "FR-1",
                "title": "Core Feature Implementation",  # Placeholder: must be dropped, not replaced
                "description": "",
                "dependencies": ["FR-2"],
            },
            {"key": "FR-7", "title": "Cart", "description": "Cart.", "dependencies": ["FR-1"], "source": "made-up"},
        ],
        "non_functional_requirements": [],  # Missing NFRs stay missing
        "clarification_questions": [],
    }

    sanitized = validate_and_sanitize_requirements_data(
        parsed=corrupted_data,
        brief="We want an e-commerce grocery delivery mobile app with search, cart, and Stripe checkout.",
        title="Grocery Delivery App",
        project_name="QuickGrocer",
    )

    frs = sanitized["functional_requirements"]
    assert [f["key"] for f in frs] == ["FR-1", "FR-2"]
    assert [f["title"] for f in frs] == ["Grocery Search", "Cart"]

    assert "Project:" not in frs[0]["description"] and "Client Brief:" not in frs[0]["description"]
    assert frs[0]["priority"] == "MEDIUM"
    assert frs[0]["acceptance_criteria"] == ["Given a product name, When searching, Then matching products are listed"]
    assert frs[0]["dependencies"] == []
    assert frs[1]["dependencies"] == ["FR-1"]

    # Source labels are normalised; unknown labels never claim the client asked for something.
    assert frs[0]["source"] == "CLIENT_STATED"
    assert frs[1]["source"] == "AI_SUGGESTED"

    assert sanitized["non_functional_requirements"] == []
    assert sanitized["assumptions"] == [] and sanitized["risks_and_dependencies"] == []
    assert "Project:" not in sanitized["overview"]["project_objective"]


def test_sanitizer_asks_instead_of_inventing_when_nothing_found():
    sanitized = validate_and_sanitize_requirements_data(parsed={"functional_requirements": []}, brief="hello")

    assert sanitized["functional_requirements"] == []
    assert sanitized["non_functional_requirements"] == []
    assert len(sanitized["clarification_questions"]) == 1
    assert sanitized["clarification_questions"][0]["context_topic"] == "Scope"


def test_offline_analyzer_does_not_invent_unrelated_requirements():
    result = analyze_brief_dynamically("Build a booking app with Google login and Stripe payments")

    text = str(result).lower()
    for invented in ("ios 15", "android api", "pci-dss", "p95", "300ms", "sendgrid", "cdn"):
        assert invented not in text
    assert result["technical_constraints"] == []
    assert any("booking" in f["title"].lower() for f in result["functional_requirements"])
