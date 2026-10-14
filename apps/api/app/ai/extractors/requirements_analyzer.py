"""Intelligent dynamic requirement analysis and extraction engine.

Transforms client briefs into structured, specific, high-quality requirements specifications
without generic placeholders or metadata leakage.
"""

from __future__ import annotations

import re
from typing import Any


def clean_metadata_leakage(text: str) -> str:
    """Strip out prompt metadata labels and markers if they leak into text."""
    if not text:
        return ""
    cleaned = text
    patterns = [
        r"^(?:Project|Analysis Title|Client Brief|Desired Outcome|Constraints|Deadline|Project Description):\s*",
        r"\b(?:Project|Analysis Title|Client Brief|Desired Outcome|Constraints|Deadline|Project Description):\s*",
    ]
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def extract_brief_and_context(user_text: str) -> dict[str, str]:
    """Parse out structured fields if user_text contains formatted prompt metadata."""
    res = {
        "project_name": "",
        "project_description": "",
        "title": "",
        "brief": user_text,
        "desired_outcome": "",
        "constraints": "",
    }

    if "Client Brief:" in user_text:
        parts = user_text.split("Client Brief:")
        header = parts[0]
        remainder = parts[1]

        # Extract project name
        proj_match = re.search(r"Project:\s*([^\n]+)", header)
        if proj_match:
            res["project_name"] = proj_match.group(1).strip()

        desc_match = re.search(r"Project Description:\s*([^\n]+)", header)
        if desc_match:
            res["project_description"] = desc_match.group(1).strip()

        title_match = re.search(r"Analysis Title:\s*([^\n]+)", header)
        if title_match:
            res["title"] = title_match.group(1).strip()

        # Extract remainder sections
        brief_text = remainder
        outcome_match = re.search(
            r"Desired Outcome:\s*([^\n]+(?:\n(?!Constraints:|Deadline:|Project Context:)[^\n]+)*)", remainder
        )
        if outcome_match:
            res["desired_outcome"] = outcome_match.group(1).strip()
            brief_text = brief_text.split("Desired Outcome:")[0]

        constraints_match = re.search(r"Constraints:\s*([^\n]+(?:\n(?!Deadline:|Project Context:)[^\n]+)*)", remainder)
        if constraints_match:
            res["constraints"] = constraints_match.group(1).strip()

        res["brief"] = brief_text.strip()
    return res


def analyze_brief_dynamically(
    brief: str,
    title: str = "",
    project_name: str = "",
    desired_outcome: str = "",
    constraints: str = "",
) -> dict[str, Any]:
    """Dynamically analyze any client brief and produce high-quality, structured requirements."""
    # Check if raw prompt was supplied
    if "Client Brief:" in brief:
        extracted = extract_brief_and_context(brief)
        brief = extracted["brief"]
        title = title or extracted["title"]
        project_name = project_name or extracted["project_name"]
        desired_outcome = desired_outcome or extracted["desired_outcome"]
        constraints = constraints or extracted["constraints"]

    brief = clean_metadata_leakage(brief).strip()
    title = clean_metadata_leakage(title).strip() or "Application Implementation"
    project_name = clean_metadata_leakage(project_name).strip() or "Software System"
    desired_outcome = clean_metadata_leakage(desired_outcome).strip()
    constraints = clean_metadata_leakage(constraints).strip()

    low = brief.lower()

    # Domain detectors
    has_auth = any(
        k in low
        for k in [
            "register",
            "log in",
            "login",
            "sign up",
            "password",
            "profile",
            "account",
            "addresses",
            "saved address",
            "credentials",
            "auth",
        ]
    )
    has_catalog = any(
        k in low for k in ["browse", "search", "filter", "product", "items", "catalog", "listing", "categories"]
    )
    has_cart = any(k in low for k in ["cart", "shopping cart", "basket", "add products", "add to cart", "quantities"])
    has_payment = any(
        k in low
        for k in ["payment", "stripe", "razorpay", "checkout", "credit card", "billing", "purchase", "online payment"]
    )
    has_order = any(k in low for k in ["order", "delivery", "shipping", "track my", "tracking"])
    has_notification = any(k in low for k in ["email", "confirmation", "notification", "push", "sms", "alert", "fcm"])
    has_admin = any(
        k in low
        for k in [
            "admin",
            "inventory",
            "manage products",
            "add, edit, and delete",
            "manage inventory",
            "stock",
            "dashboard",
            "update order status",
        ]
    )

    # Non-e-commerce domains
    has_booking = any(
        k in low for k in ["appointment", "booking", "schedule", "calendar", "time slot", "doctor", "availability"]
    )
    has_messaging = any(k in low for k in ["chat", "messaging", "comment", "discussion", "collaboration", "real-time"])
    has_analytics = any(
        k in low for k in ["report", "analytics", "metrics", "export", "dashboard metrics", "chart", "statistics"]
    )

    functional_requirements: list[dict[str, Any]] = []

    # 1. Authentication
    if has_auth:
        fr_auth = {
            "key": "",
            "title": "User Accounts & Sign-in",
            "description": "Users can create an account, sign in and manage their profile. The sign-in method is as described in the brief.",
            "priority": "HIGH",
            "acceptance_criteria": [
                "Given a new visitor, When they register, Then an account is created and they are signed in.",
                "Given a registered user, When they sign in, Then they can access their account features.",
                "Given a signed-in user, When they update their profile, Then the changes are saved.",
            ],
            "dependencies": [],
            "open_questions": [],
            "source": "CLIENT_STATED",
            "domain_tag": "AUTH",
        }
        functional_requirements.append(fr_auth)

    # 2. Product Catalog
    if has_catalog:
        fr_catalog = {
            "key": "",
            "title": "Product Catalog Browsing, Search & Filtering",
            "description": "Customers can browse, search and filter products and see their details.",
            "priority": "HIGH",
            "acceptance_criteria": [
                "Given the product catalog, When a user searches or filters, Then matching products are listed.",
                "Given a selected product, When navigating to the item details, Then comprehensive descriptions, current pricing, and stock status are displayed.",
                "Given a search query with no matching items, When submitted, Then a helpful empty state with suggested categories is presented.",
            ],
            "dependencies": [],
            "open_questions": [],
            "source": "CLIENT_STATED",
            "domain_tag": "CATALOG",
        }
        functional_requirements.append(fr_catalog)

    # 3. Shopping Cart
    if has_cart:
        fr_cart = {
            "key": "",
            "title": "Shopping Cart & Quantity Management",
            "description": "Provide an interactive shopping cart allowing customers to add products, adjust quantities, review itemized prices, and remove items with dynamic subtotal recalculation.",
            "priority": "HIGH",
            "acceptance_criteria": [
                "Given an in-stock product, When added to the shopping cart, Then the cart counter updates immediately and the item appears in the cart overview.",
                "Given items in the cart, When the user modifies quantities or removes an item, Then line-item subtotals, taxes, and order totals update dynamically.",
                "Given an out-of-stock product, When a customer attempts to add it to the cart, Then an informative stock limit notice is displayed.",
            ],
            "dependencies": [],
            "open_questions": [],
            "source": "CLIENT_STATED",
            "domain_tag": "CART",
        }
        functional_requirements.append(fr_cart)

    # 4. Payment Processing
    if has_payment:
        gateways = (
            "Stripe or Razorpay"
            if ("stripe" in low and "razorpay" in low)
            else ("Stripe" if "stripe" in low else ("Razorpay" if "razorpay" in low else "secure payment gateway"))
        )
        fr_payment = {
            "key": "",
            "title": "Secure Payment Processing & Checkout Integration",
            "description": f"Facilitate secure online payments via {gateways} with tokenized card processing, handling payment authorization, failures, and order confirmation.",
            "priority": "HIGH",
            "acceptance_criteria": [
                "Given an active cart and valid delivery address, When initiating checkout with valid payment credentials, Then payment is authorized via the payment gateway and an order confirmation is generated.",
                "Given a rejected or declined transaction, When payment fails, Then a clear user-friendly error message is displayed and no order charge is finalized.",
                "Given payment details, When submitted during checkout, Then raw card data is securely tokenized through the provider SDK without being stored directly in the database.",
            ],
            "dependencies": [],
            "open_questions": [],
            "source": "CLIENT_STATED",
            "domain_tag": "PAYMENT",
        }
        functional_requirements.append(fr_payment)

    # 5. Order Tracking & History
    if has_order:
        fr_order = {
            "key": "",
            "title": "Order History & Status",
            "description": "Customers can see their orders and follow their status.",
            "priority": "HIGH",
            "acceptance_criteria": [
                "Given an authenticated customer, When viewing their order history, Then all past purchases with item summaries, timestamps, and current delivery statuses are displayed.",
                "Given a placed order, When the customer checks it, Then its current status is shown.",
                "Given an order that may still be cancelled, When the customer cancels it, Then it is marked as cancelled (policy to be confirmed).",
            ],
            "dependencies": [],
            "open_questions": [],
            "source": "CLIENT_STATED",
            "domain_tag": "ORDER",
        }
        functional_requirements.append(fr_order)

    # 6. Notifications
    if has_notification:
        fr_notif = {
            "key": "",
            "title": "Automated Notifications",
            "description": "Send automated notifications for the events named in the brief (channels to be confirmed).",
            "priority": "MEDIUM",
            "acceptance_criteria": [
                "Given a completed purchase, When checkout finishes, Then a confirmation is sent to the customer.",
                "Given a notifiable event, When it occurs, Then the user is notified through the agreed channel.",
            ],
            "dependencies": [],
            "open_questions": [],
            "source": "CLIENT_STATED",
            "domain_tag": "NOTIFICATION",
        }
        functional_requirements.append(fr_notif)

    # 7. Admin Dashboard & Inventory
    if has_admin:
        fr_admin = {
            "key": "",
            "title": "Admin Dashboard: Product Catalog & Inventory Management",
            "description": "Provide administrative controls for staff to add, edit, and delete products, manage inventory stock counts, review incoming customer orders, and update order statuses.",
            "priority": "HIGH",
            "acceptance_criteria": [
                "Given an authenticated administrator, When adding, editing, or deleting a product, Then inventory data updates immediately across client applications.",
                "Given customer orders pending fulfillment, When an admin updates the status to SHIPPED or COMPLETED, Then status changes persist and trigger customer notifications.",
                "Given an admin, When they view orders, Then they can update each order's status.",
            ],
            "dependencies": [],
            "open_questions": [],
            "source": "CLIENT_STATED",
            "domain_tag": "ADMIN",
        }
        functional_requirements.append(fr_admin)

    # 8. Booking Domain
    if has_booking:
        fr_booking = {
            "key": "",
            "title": "Appointment Booking & Availability Scheduling",
            "description": "Enable users to browse available provider time slots, reserve appointments, and manage upcoming bookings.",
            "priority": "HIGH",
            "acceptance_criteria": [
                "Given an authenticated user viewing a provider schedule, When selecting an open slot, Then the booking is reserved and the slot is locked from concurrent booking.",
                "Given an existing appointment, When cancelling or rescheduling with adequate advance notice, Then calendar availability updates and confirmation is dispatched.",
            ],
            "dependencies": [],
            "open_questions": [],
            "source": "CLIENT_STATED",
            "domain_tag": "BOOKING",
        }
        functional_requirements.append(fr_booking)

    # 9. Messaging Domain
    if has_messaging:
        fr_msg = {
            "key": "",
            "title": "Real-Time Messaging & Communication Channels",
            "description": "Facilitate real-time communications and discussions with instant delivery and persistent message history.",
            "priority": "MEDIUM",
            "acceptance_criteria": [
                "Given active chat participants, When a message is sent, Then recipient receives the message in real-time with delivery acknowledgement.",
                "Given conversation history, When a user opens the chat, Then previous messages load in chronological order.",
            ],
            "dependencies": [],
            "open_questions": [],
            "source": "CLIENT_STATED",
            "domain_tag": "MESSAGING",
        }
        functional_requirements.append(fr_msg)

    # 10. Analytics Domain
    if has_analytics:
        fr_analytics = {
            "key": "",
            "title": "Operational Analytics, Metrics & Export Reporting",
            "description": "Generate aggregated business intelligence reports, operational metrics dashboards, and exportable data files.",
            "priority": "MEDIUM",
            "acceptance_criteria": [
                "Given recorded platform activity, When viewing the analytics dashboard, Then key performance indicators and graphical summaries render accurately.",
                "Given a filtered date range, When exporting data, Then a formatted CSV or PDF export is generated.",
            ],
            "dependencies": [],
            "open_questions": [],
            "source": "CLIENT_STATED",
            "domain_tag": "ANALYTICS",
        }
        functional_requirements.append(fr_analytics)

    # Dynamic Fallback: if no domain matched, extract from sentences
    if not functional_requirements:
        sentences = [s.strip() for s in re.split(r"[.!?]+", brief) if len(s.strip()) > 15]

        for idx, sentence in enumerate(sentences[:4], start=1):
            short_title = sentence[:45].strip()
            if len(short_title) > 40:
                short_title = short_title.rsplit(" ", 1)[0]
            functional_requirements.append(
                {
                    "key": "",
                    "title": f"Feature: {short_title.title()}",
                    "description": sentence,
                    "priority": "HIGH" if idx == 1 else "MEDIUM",
                    "acceptance_criteria": [],
                    "dependencies": [],
                    "open_questions": [],
                    "source": "CLIENT_STATED",
                    "domain_tag": f"CUSTOM_{idx}",
                }
            )

    # Assign sequential keys and resolve legitimate prerequisites
    domain_to_key: dict[str, str] = {}
    for i, req in enumerate(functional_requirements, start=1):
        key = f"FR-{i}"
        req["key"] = key
        domain_tag = req.pop("domain_tag", "")
        domain_to_key[domain_tag] = key

    # Calculate logical dependencies based on domain relationships
    for req in functional_requirements:
        key = req["key"]
        deps: list[str] = []
        if "Cart" in req["title"] and "AUTH" in domain_to_key and domain_to_key["AUTH"] != key:
            deps.append(domain_to_key["AUTH"])
        elif "Checkout" in req["title"] or "Payment" in req["title"]:
            if "CART" in domain_to_key and domain_to_key["CART"] != key:
                deps.append(domain_to_key["CART"])
            elif "CATALOG" in domain_to_key and domain_to_key["CATALOG"] != key:
                deps.append(domain_to_key["CATALOG"])
        elif "Order" in req["title"]:
            if "PAYMENT" in domain_to_key and domain_to_key["PAYMENT"] != key:
                deps.append(domain_to_key["PAYMENT"])
        elif "Notification" in req["title"]:
            if "ORDER" in domain_to_key and domain_to_key["ORDER"] != key:
                deps.append(domain_to_key["ORDER"])
            elif "PAYMENT" in domain_to_key and domain_to_key["PAYMENT"] != key:
                deps.append(domain_to_key["PAYMENT"])
        elif "Admin" in req["title"] and "AUTH" in domain_to_key and domain_to_key["AUTH"] != key:
            deps.append(domain_to_key["AUTH"])

        # Only keep valid earlier keys
        curr_idx = int(key.split("-")[1])
        valid_deps = [d for d in deps if int(d.split("-")[1]) < curr_idx]
        req["dependencies"] = valid_deps

    has_security = (
        has_auth or has_payment or any(k in low for k in ["secure", "security", "privacy", "gdpr", "encrypt"])
    )
    has_performance = any(k in low for k in ["fast", "quick", "performance", "speed", "scalable", "load", "concurrent"])
    has_mobile = any(k in low for k in ["mobile", "android", "ios", "iphone", "phone", "app store", "play store"])
    has_reliability = any(k in low for k in ["reliable", "reliability", "uptime", "high availability", "backup"])

    # Non-functional requirements: only qualities the brief points to. No invented thresholds.
    non_functional_requirements: list[dict[str, Any]] = []

    def add_nfr(title: str, category: str, description: str, stated: bool) -> None:
        non_functional_requirements.append(
            {
                "key": f"NFR-{len(non_functional_requirements) + 1}",
                "title": title,
                "category": category,
                "description": description,
                "priority": "HIGH",
                "source": "CLIENT_STATED" if stated else "AI_SUGGESTED",
            }
        )

    if has_security:
        add_nfr(
            "Data Protection",
            "SECURITY",
            "User credentials and any payment data must be protected; card data must be handled by the payment "
            "provider rather than stored by the system.",
            stated=any(k in low for k in ["secure", "security", "privacy", "encrypt"]),
        )
    if has_performance:
        add_nfr(
            "Responsiveness",
            "PERFORMANCE",
            "Key user flows must feel fast. The client has not given a measurable target yet (see clarification questions).",
            stated=True,
        )
    if has_mobile:
        add_nfr(
            "Mobile Support",
            "COMPATIBILITY",
            "The product must work on mobile devices. Supported platforms and versions are still to be confirmed.",
            stated=True,
        )
    if has_reliability:
        add_nfr(
            "Reliability",
            "RELIABILITY",
            "The system must stay available and recover gracefully from failures.",
            stated=True,
        )

    # Technical constraints: only what the developer/client wrote in the constraints field.
    tech_constraints = []
    for c in [x.strip() for x in constraints.split(",") if x.strip()]:
        c_low = c.lower()
        if any(k in c_low for k in ["react", "vue", "ios", "android", "mobile", "next", "flutter"]):
            cat = "FRONTEND"
        elif any(k in c_low for k in ["node", "express", "python", "fastapi", "django"]):
            cat = "BACKEND"
        elif any(k in c_low for k in ["postgres", "sql", "mongo", "redis"]):
            cat = "DATABASE"
        elif any(k in c_low for k in ["stripe", "razorpay", "paypal"]):
            cat = "PAYMENT"
        else:
            cat = "GENERAL"
        tech_constraints.append({"constraint": c, "category": cat, "source": "CLIENT_STATED"})

    # Assumptions: only those needed by capabilities the brief mentions.
    assumptions = []
    if has_payment:
        assumptions.append(
            {
                "description": "The client will provide payment gateway accounts and API credentials (test and live).",
                "reason": "Payment integration cannot be built or tested without them.",
                "confidence": "HIGH",
            }
        )
    if has_notification:
        assumptions.append(
            {
                "description": "An email/notification delivery service will be available for automated messages.",
                "reason": "The brief asks for notifications or confirmations.",
                "confidence": "MEDIUM",
            }
        )

    # Clarification questions: targeted at gaps in *this* brief.
    clarification_questions: list[dict[str, Any]] = []

    def ask(question: str, reason: str, topic: str) -> None:
        clarification_questions.append(
            {
                "question_key": f"Q-{len(clarification_questions) + 1}",
                "question": question,
                "reason": reason,
                "context_topic": topic,
            }
        )

    if not functional_requirements:
        ask(
            "What should the system do? Please describe the main features or user tasks it must support.",
            "The brief does not describe concrete functionality, so no requirements could be identified.",
            "Scope",
        )
    has_date = bool(
        re.search(
            r"\b(\d{1,2}[/-]\d{1,2}|\d{4}-\d{2}|week|month|january|february|march|april|may|june|july|"
            r"august|september|october|november|december|christmas|q[1-4])\b",
            low,
        )
    )
    if not has_date or "maybe" in low or "?" in brief:
        ask(
            "What is the firm target launch date, and is it fixed or flexible?",
            "No firm deadline is given in the brief.",
            "Timeline",
        )
    if has_payment and not any(k in low for k in ["stripe", "razorpay", "paypal", "braintree"]):
        ask("Which payment provider should be used?", "Payments are required but no provider is named.", "Payments")
    if has_performance:
        ask(
            "What does 'fast' mean for you in measurable terms (e.g. page load time, number of concurrent users)?",
            "Performance is requested without a measurable target.",
            "Performance",
        )
    if has_mobile:
        ask(
            "Should this be a native mobile app, a mobile-friendly website, or both? Which platforms?",
            "Mobile use is mentioned without specifying the platform.",
            "Platforms",
        )
    if has_order:
        ask(
            "Can customers cancel or change orders, and until when?",
            "Order handling is mentioned but the cancellation policy is not.",
            "Orders",
        )
    if has_notification:
        ask(
            "Which events should trigger notifications, and through which channels (email, SMS, push)?",
            "Notifications are requested without specifying triggers or channels.",
            "Notifications",
        )

    # Risks: only for capabilities that carry a known delivery risk.
    risks = []
    if has_payment:
        risks.append(
            {
                "description": "Payment confirmations can arrive late or twice (webhooks), causing wrong order states.",
                "risk_type": "INTEGRATION",
                "severity": "MEDIUM",
                "mitigation": "Process payment webhooks idempotently and reconcile pending payments.",
            }
        )
    if has_admin and (has_cart or has_order):
        risks.append(
            {
                "description": "Two customers may buy the last item in stock at the same time.",
                "risk_type": "TECHNICAL",
                "severity": "MEDIUM",
                "mitigation": "Reserve stock atomically during checkout.",
            }
        )

    overview = {
        "project_objective": title or project_name,
        "business_problem": "",
        "intended_outcome": desired_outcome,
        "in_scope": [req["title"] for req in functional_requirements],
        "out_of_scope": [],
    }

    return {
        "overview": overview,
        "functional_requirements": functional_requirements,
        "non_functional_requirements": non_functional_requirements,
        "technical_constraints": tech_constraints,
        "assumptions": assumptions,
        "clarification_questions": clarification_questions,
        "risks_and_dependencies": risks,
    }


SOURCES = {"CLIENT_STATED", "AI_SUGGESTED"}

NO_FUNCTIONALITY_QUESTION = {
    "question_key": "Q-1",
    "question": "What should the system do? Please describe the main features or user tasks it must support.",
    "reason": "The brief does not describe concrete functionality, so no requirements could be identified.",
    "context_topic": "Scope",
}


def _source(item: dict[str, Any]) -> str:
    """Unlabelled items are treated as suggestions: we never assume the client asked for something."""
    value = str(item.get("source", "")).upper().strip()
    return value if value in SOURCES else "AI_SUGGESTED"


def validate_and_sanitize_requirements_data(
    parsed: dict[str, Any],
    brief: str = "",
    project_name: str = "",
    title: str = "",
    desired_outcome: str = "",
    constraints: str = "",
) -> dict[str, Any]:
    """Clean and validate AI-generated requirements without adding any content of our own.

    - Removes leaked prompt metadata from text.
    - Drops empty/placeholder items instead of replacing them with templates.
    - Enforces sequential keys (FR-1.., NFR-1.., Q-1..) and valid, earlier-only dependencies.
    - Labels every requirement and constraint with its source (CLIENT_STATED / AI_SUGGESTED).
    - If nothing concrete was found, asks the client a clarification question rather than inventing scope.
    """
    if not isinstance(parsed, dict):
        raise ValueError("Requirements analysis output must be a JSON object")

    generic_titles = {
        "core feature implementation",
        "api validation and data persistence",
        "feature implementation",
        "system integration",
        "default feature",
        "requirement 1",
        "requirement 2",
        "core functionality",
    }
    generic_criteria = (
        "when input is supplied, expected result is returned",
        "given valid payload, when submitted, record is stored",
        "expected outcome occurs",
    )

    def as_list(value: Any) -> list[Any]:
        return value if isinstance(value, list) else []

    # Functional requirements
    kept_frs = []
    for fr in as_list(parsed.get("functional_requirements")):
        if not isinstance(fr, dict):
            continue
        fr_title = clean_metadata_leakage(str(fr.get("title", ""))).strip()
        fr_desc = clean_metadata_leakage(str(fr.get("description", ""))).strip()
        if not fr_title or fr_title.lower() in generic_titles:
            continue  # A placeholder carries no information; dropping it is more honest than filling it in.
        kept_frs.append((fr, fr_title, fr_desc or fr_title))

    sanitized_frs: list[dict[str, Any]] = []
    for i, (fr, fr_title, fr_desc) in enumerate(kept_frs, start=1):
        criteria = []
        for crit in as_list(fr.get("acceptance_criteria")):
            c_str = clean_metadata_leakage(str(crit)).strip()
            if not c_str or any(g in c_str.lower() for g in generic_criteria):
                continue
            c_norm = re.sub(r",\s*when\s+", ", When ", c_str, flags=re.IGNORECASE)
            c_norm = re.sub(r",\s*then\s+", ", Then ", c_norm, flags=re.IGNORECASE)
            if c_norm.lower().startswith("given "):
                c_norm = "Given " + c_norm[6:]
            else:
                c_norm = f"Given {c_norm}"
            criteria.append(c_norm)

        deps = []
        for dep in as_list(fr.get("dependencies")):
            match = re.match(r"^FR-(\d+)$", str(dep).strip().upper())
            if match and 1 <= int(match.group(1)) < i:
                deps.append(f"FR-{int(match.group(1))}")

        priority = str(fr.get("priority", "MEDIUM")).upper()
        sanitized_frs.append(
            {
                "key": f"FR-{i}",
                "title": fr_title,
                "description": fr_desc,
                "priority": priority if priority in ("LOW", "MEDIUM", "HIGH", "URGENT", "CRITICAL") else "MEDIUM",
                "acceptance_criteria": criteria,
                "dependencies": deps,
                "open_questions": as_list(fr.get("open_questions")),
                "source": _source(fr),
            }
        )

    # Non-functional requirements
    sanitized_nfrs: list[dict[str, Any]] = []
    for nfr in as_list(parsed.get("non_functional_requirements")):
        if not isinstance(nfr, dict):
            continue
        n_title = clean_metadata_leakage(str(nfr.get("title", ""))).strip()
        n_desc = clean_metadata_leakage(str(nfr.get("description", ""))).strip()
        if not n_title and not n_desc:
            continue
        n_prio = str(nfr.get("priority", "MEDIUM")).upper()
        sanitized_nfrs.append(
            {
                "key": f"NFR-{len(sanitized_nfrs) + 1}",
                "title": n_title or n_desc[:60],
                "category": str(nfr.get("category", "GENERAL")).upper(),
                "description": n_desc or n_title,
                "priority": n_prio if n_prio in ("LOW", "MEDIUM", "HIGH", "URGENT", "CRITICAL") else "MEDIUM",
                "source": _source(nfr),
            }
        )

    # Clarification questions
    sanitized_questions: list[dict[str, Any]] = []
    for q in as_list(parsed.get("clarification_questions")):
        if not isinstance(q, dict):
            continue
        q_text = clean_metadata_leakage(str(q.get("question", ""))).strip()
        if q_text:
            sanitized_questions.append(
                {
                    "question_key": f"Q-{len(sanitized_questions) + 1}",
                    "question": q_text,
                    "reason": clean_metadata_leakage(str(q.get("reason", ""))).strip() or None,
                    "context_topic": clean_metadata_leakage(str(q.get("context_topic", ""))).strip() or None,
                }
            )
    if not sanitized_frs and not sanitized_questions:
        sanitized_questions = [dict(NO_FUNCTIONALITY_QUESTION)]

    technical_constraints = []
    for tc in as_list(parsed.get("technical_constraints")):
        if isinstance(tc, dict) and str(tc.get("constraint", "")).strip():
            technical_constraints.append(
                {
                    "constraint": clean_metadata_leakage(str(tc["constraint"])).strip(),
                    "category": str(tc.get("category", "GENERAL")).upper(),
                    "source": _source(tc),
                }
            )

    raw_overview = parsed.get("overview")
    source_overview: dict[str, Any] = raw_overview if isinstance(raw_overview, dict) else {}
    overview = {
        "project_objective": clean_metadata_leakage(str(source_overview.get("project_objective", ""))).strip() or title,
        "business_problem": clean_metadata_leakage(str(source_overview.get("business_problem", ""))).strip(),
        "intended_outcome": clean_metadata_leakage(str(source_overview.get("intended_outcome", ""))).strip()
        or desired_outcome,
        "in_scope": as_list(source_overview.get("in_scope")) or [f["title"] for f in sanitized_frs],
        "out_of_scope": as_list(source_overview.get("out_of_scope")),
    }

    return {
        "overview": overview,
        "functional_requirements": sanitized_frs,
        "non_functional_requirements": sanitized_nfrs,
        "technical_constraints": technical_constraints,
        "assumptions": [a for a in as_list(parsed.get("assumptions")) if isinstance(a, dict) and a.get("description")],
        "clarification_questions": sanitized_questions,
        "risks_and_dependencies": [
            r for r in as_list(parsed.get("risks_and_dependencies")) if isinstance(r, dict) and r.get("description")
        ],
    }
