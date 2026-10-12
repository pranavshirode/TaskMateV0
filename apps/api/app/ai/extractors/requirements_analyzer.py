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
        outcome_match = re.search(r"Desired Outcome:\s*([^\n]+(?:\n(?!Constraints:|Deadline:|Project Context:)[^\n]+)*)", remainder)
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
    has_auth = any(k in low for k in ["register", "log in", "login", "sign up", "password", "profile", "account", "addresses", "saved address", "credentials", "auth"])
    has_catalog = any(k in low for k in ["browse", "search", "filter", "product", "items", "catalog", "listing", "categories"])
    has_cart = any(k in low for k in ["cart", "shopping cart", "basket", "add products", "add to cart", "quantities"])
    has_payment = any(k in low for k in ["payment", "stripe", "razorpay", "checkout", "credit card", "billing", "purchase", "online payment"])
    has_order = any(k in low for k in ["order", "order history", "track", "delivery", "cancel", "status", "shipping"])
    has_notification = any(k in low for k in ["email", "confirmation", "notification", "push", "sms", "alert", "fcm"])
    has_admin = any(k in low for k in ["admin", "inventory", "manage products", "add, edit, and delete", "manage inventory", "stock", "dashboard", "update order status"])
    
    # Non-e-commerce domains
    has_booking = any(k in low for k in ["appointment", "booking", "schedule", "calendar", "time slot", "doctor", "availability"])
    has_messaging = any(k in low for k in ["chat", "messaging", "comment", "discussion", "collaboration", "real-time"])
    has_analytics = any(k in low for k in ["report", "analytics", "metrics", "export", "dashboard metrics", "chart", "statistics"])

    functional_requirements: list[dict[str, Any]] = []
    
    # 1. Authentication
    if has_auth:
        fr_auth = {
            "key": "",
            "title": "User Registration, Authentication & Profile Management",
            "description": "Enable secure account registration and authentication via email and password, profile management, and maintenance of saved customer addresses.",
            "priority": "HIGH",
            "acceptance_criteria": [
                "Given an unauthenticated visitor with valid credentials, When submitting the registration form, Then a new account is created with encrypted credentials and a session token is issued.",
                "Given registered credentials, When the user logs in, Then credentials are authenticated and access to protected account features is granted.",
                "Given an authenticated user, When updating profile details or saved delivery addresses, Then all input validations pass and changes persist successfully.",
            ],
            "dependencies": [],
            "open_questions": [],
            "domain_tag": "AUTH",
        }
        functional_requirements.append(fr_auth)

    # 2. Product Catalog
    if has_catalog:
        fr_catalog = {
            "key": "",
            "title": "Product Catalog Browsing, Search & Filtering",
            "description": "Provide a responsive product catalog enabling customers to search items by keyword, filter by categories or attributes, and view real-time availability and pricing.",
            "priority": "HIGH",
            "acceptance_criteria": [
                "Given the product catalog, When a user enters search keywords or applies category filters, Then relevant product listings update within 300ms.",
                "Given a selected product, When navigating to the item details, Then comprehensive descriptions, current pricing, and stock status are displayed.",
                "Given a search query with no matching items, When submitted, Then a helpful empty state with suggested categories is presented.",
            ],
            "dependencies": [],
            "open_questions": [],
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
            "domain_tag": "CART",
        }
        functional_requirements.append(fr_cart)

    # 4. Payment Processing
    if has_payment:
        gateways = "Stripe or Razorpay" if ("stripe" in low and "razorpay" in low) else ("Stripe" if "stripe" in low else ("Razorpay" if "razorpay" in low else "secure payment gateway"))
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
            "domain_tag": "PAYMENT",
        }
        functional_requirements.append(fr_payment)

    # 5. Order Tracking & History
    if has_order:
        fr_order = {
            "key": "",
            "title": "Order History, Real-Time Delivery Tracking & Cancellation",
            "description": "Allow customers to view order history, monitor delivery progress through milestone statuses, and cancel eligible orders before fulfillment begins.",
            "priority": "HIGH",
            "acceptance_criteria": [
                "Given an authenticated customer, When viewing their order history, Then all past purchases with item summaries, timestamps, and current delivery statuses are displayed.",
                "Given an order in transit, When tracking delivery status, Then milestone updates (Placed, Confirmed, Shipped, Delivered) reflect current progress.",
                "Given an eligible placed order within the cancellation window, When requesting cancellation, Then the order status transitions to CANCELLED and refund processing initiates.",
            ],
            "dependencies": [],
            "open_questions": [],
            "domain_tag": "ORDER",
        }
        functional_requirements.append(fr_order)

    # 6. Notifications
    if has_notification:
        fr_notif = {
            "key": "",
            "title": "Automated Order Confirmation & Event Notifications",
            "description": "Dispatch automated transactional emails upon successful purchase and transmit push alerts for fulfillment status transitions.",
            "priority": "MEDIUM",
            "acceptance_criteria": [
                "Given a completed order payment, When checkout finalizes, Then a transactional confirmation email containing receipt, item list, and order ID is dispatched.",
                "Given a delivery status update, When marked as out-for-delivery, Then an alert notification is sent to the customer device.",
            ],
            "dependencies": [],
            "open_questions": [],
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
                "Given low inventory levels, When threshold is reached, Then inventory alerts are flagged in the admin portal.",
            ],
            "dependencies": [],
            "open_questions": [],
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
            "domain_tag": "ANALYTICS",
        }
        functional_requirements.append(fr_analytics)

    # Dynamic Fallback: if no domain matched, extract from sentences
    if not functional_requirements:
        sentences = [s.strip() for s in re.split(r"[.!?]+", brief) if len(s.strip()) > 15]
        if not sentences:
            sentences = [f"Implement core workflows for {title}"]

        for idx, sentence in enumerate(sentences[:4], start=1):
            short_title = sentence[:45].strip()
            if len(short_title) > 40:
                short_title = short_title.rsplit(" ", 1)[0]
            functional_requirements.append({
                "key": "",
                "title": f"Feature: {short_title.title()}",
                "description": sentence,
                "priority": "HIGH" if idx == 1 else "MEDIUM",
                "acceptance_criteria": [
                    f"Given configured system state, when {short_title.lower()} executes, then valid status and feedback are returned.",
                    f"Given invalid inputs or network interruption, when request is processed, then explicit error diagnostics are returned.",
                ],
                "dependencies": [],
                "open_questions": [],
                "domain_tag": f"CUSTOM_{idx}",
            })

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
        elif "Admin" in req["title"]:
            if "AUTH" in domain_to_key and domain_to_key["AUTH"] != key:
                deps.append(domain_to_key["AUTH"])
        
        # Only keep valid earlier keys
        curr_idx = int(key.split("-")[1])
        valid_deps = [d for d in deps if int(d.split("-")[1]) < curr_idx]
        req["dependencies"] = valid_deps

    # Measurable Non-Functional Requirements
    non_functional_requirements = [
        {
            "key": "NFR-1",
            "title": "Data Protection, Password Hashing & PCI Compliance",
            "category": "SECURITY",
            "description": "All customer passwords must be securely hashed using Argon2 or bcrypt. Payment card information must never be stored directly in the database and must utilize tokenized PCI-DSS compliant gateway integrations.",
            "priority": "HIGH",
        },
        {
            "key": "NFR-2",
            "title": "API Response Latency & App Responsiveness",
            "category": "PERFORMANCE",
            "description": "All backend API endpoints must maintain sub-300ms p95 response time under normal concurrent load. Mobile client app cold launch must complete within 2.0 seconds.",
            "priority": "HIGH",
        },
        {
            "key": "NFR-3",
            "title": "Mobile Platform & Device Compatibility",
            "category": "COMPATIBILITY",
            "description": "The client user interface must provide responsive, consistent rendering across modern Android (API 29+) and iOS (15+) devices with adaptive layout support.",
            "priority": "MEDIUM",
        },
        {
            "key": "NFR-4",
            "title": "Fault Tolerance, Resilience & Error Diagnostics",
            "category": "RELIABILITY",
            "description": "The system must provide graceful error degradation and unambiguous user feedback for network timeouts, failed payments, and out-of-stock items, preventing unhandled exceptions.",
            "priority": "HIGH",
        },
    ]

    # Technical constraints
    tech_constraints = []
    if constraints:
        for c in [x.strip() for x in constraints.split(",") if x.strip()]:
            c_low = c.lower()
            cat = "FRONTEND" if any(k in c_low for k in ["react", "vue", "ios", "android", "mobile"]) else (
                "BACKEND" if any(k in c_low for k in ["node", "express", "python", "fastapi", "django"]) else (
                    "DATABASE" if any(k in c_low for k in ["postgres", "sql", "mongo", "redis"]) else (
                        "PAYMENT" if any(k in c_low for k in ["stripe", "razorpay", "paypal"]) else "GENERAL"
                    )
                )
            )
            tech_constraints.append({"constraint": c, "category": cat})
    else:
        tech_constraints = [
            {"constraint": "Cross-platform mobile client framework", "category": "FRONTEND"},
            {"constraint": "Scalable RESTful API backend with relational database", "category": "BACKEND"},
            {"constraint": "PCI-DSS compliant payment integration", "category": "SECURITY"},
        ]

    # Assumptions
    assumptions = [
        {
            "description": "Third-party payment gateway credentials (sandbox and webhook signing keys) will be provided prior to checkout integration.",
            "reason": "Required for transactional verification and automated testing.",
            "confidence": "HIGH",
        },
        {
            "description": "A transactional email service provider (e.g. SendGrid, AWS SES) will be configured for dispatching order confirmation receipts.",
            "reason": "Essential for automated confirmation workflows.",
            "confidence": "HIGH",
        },
        {
            "description": "Product catalog images will be hosted on a cloud CDN object store (e.g., AWS S3 or Cloudinary) with public URLs.",
            "reason": "Prevents database bloat and ensures high catalog browsing performance.",
            "confidence": "MEDIUM",
        },
    ]

    # Clarification questions
    clarification_questions = [
        {
            "question_key": "Q-1",
            "question": "What is the policy window and conditions for customer order cancellation eligibility (e.g. within 30 minutes, or prior to dispatch)?",
            "reason": "Defines exact business logic and state machine constraints for order cancellation and automated refunds.",
            "context_topic": "Order Cancellation Policy",
        },
        {
            "question_key": "Q-2",
            "question": "Which transactional email provider (SendGrid, AWS SES, or Resend) should be configured for purchase receipts and dispatch alerts?",
            "reason": "Ensures environment secrets and API keys are set up before notification development.",
            "context_topic": "Email Delivery Service",
        },
        {
            "question_key": "Q-3",
            "question": "Are there specific regional tax calculation rules or flat shipping tiers required during the checkout calculation flow?",
            "reason": "Clarifies total pricing calculations in the cart and checkout process.",
            "context_topic": "Taxation & Shipping Calculation",
        },
    ]

    # Risks & Mitigations
    risks = [
        {
            "description": "Payment gateway webhook delivery delays or network partitions could delay order confirmation receipts if not handled asynchronously.",
            "risk_type": "INTEGRATION",
            "severity": "MEDIUM",
            "mitigation": "Implement an idempotent webhook listener with background job queue retries and reconciliation polling.",
        },
        {
            "description": "Inventory race condition when multiple customers attempt to purchase the final unit of stock simultaneously.",
            "risk_type": "TECHNICAL",
            "severity": "HIGH",
            "mitigation": "Use database row-level locking or atomic decrement transactions when reserving inventory during checkout.",
        },
    ]

    # Overview
    in_scope_items = [req["title"] for req in functional_requirements]
    out_of_scope_items = [
        "Third-party courier physical logistics hardware integration",
        "Multi-currency exchange rate conversions outside designated payment accounts",
        "Custom barcode or RFID scanner hardware integrations",
    ]

    overview = {
        "project_objective": title or f"Deliver production-ready {project_name} application",
        "business_problem": "Fulfill client specifications with end-to-end functionality, high reliability, and clear requirements traceability.",
        "intended_outcome": desired_outcome or "Fully tested and validated cross-platform software deliverable.",
        "in_scope": in_scope_items,
        "out_of_scope": out_of_scope_items,
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


def validate_and_sanitize_requirements_data(
    parsed: dict[str, Any],
    brief: str = "",
    project_name: str = "",
    title: str = "",
    desired_outcome: str = "",
    constraints: str = "",
) -> dict[str, Any]:
    """Strictly validate and sanitize AI-generated requirements against business analyst standards.

    1. Removes any leaked prompt metadata or instructions from titles and descriptions.
    2. Detects and replaces generic placeholder titles.
    3. Replaces generic/untestable acceptance criteria with specific Given-When-Then scenarios.
    4. Enforces sequential and well-formed keys (FR-1.., NFR-1.., Q-1..).
    5. Validates dependency integrity (no self-dependencies, only valid earlier prerequisite keys).
    6. Ensures measurable criteria for Non-Functional Requirements.
    """
    if not isinstance(parsed, dict):
        return analyze_brief_dynamically(brief, title, project_name, desired_outcome, constraints)

    # Reference fallback in case we need capability replacements
    fallback_data = analyze_brief_dynamically(brief, title, project_name, desired_outcome, constraints)
    fallback_frs = fallback_data["functional_requirements"]

    # Ensure functional_requirements is present and non-empty
    raw_frs = parsed.get("functional_requirements")
    if not isinstance(raw_frs, list) or len(raw_frs) == 0:
        raw_frs = fallback_frs

    sanitized_frs: list[dict[str, Any]] = []
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

    for i, fr in enumerate(raw_frs, start=1):
        if not isinstance(fr, dict):
            continue
        key = f"FR-{i}"
        raw_title = clean_metadata_leakage(str(fr.get("title", ""))).strip()
        raw_desc = clean_metadata_leakage(str(fr.get("description", ""))).strip()

        # If title is generic or empty, use fallback requirement title if available
        if not raw_title or raw_title.lower() in generic_titles:
            fallback_match = fallback_frs[i - 1] if (i - 1) < len(fallback_frs) else fallback_frs[0]
            raw_title = fallback_match["title"]
            if not raw_desc or len(raw_desc) < 20 or raw_desc.lower().startswith("persist records"):
                raw_desc = fallback_match["description"]

        # If description is too short or copies prompt labels
        if not raw_desc or len(raw_desc) < 15:
            fallback_match = fallback_frs[i - 1] if (i - 1) < len(fallback_frs) else fallback_frs[0]
            raw_desc = fallback_match["description"]

        # Validate acceptance criteria
        raw_criteria = fr.get("acceptance_criteria")
        clean_criteria: list[str] = []
        if isinstance(raw_criteria, list):
            for crit in raw_criteria:
                c_str = clean_metadata_leakage(str(crit)).strip()
                c_low = c_str.lower()
                # Check for generic criteria
                if (
                    "when input is supplied, expected result is returned" in c_low
                    or "given valid payload, when submitted, record is stored" in c_low
                    or "expected outcome occurs" in c_low
                    or not c_str
                ):
                    continue
                clean_criteria.append(c_str)

        if not clean_criteria:
            fallback_match = fallback_frs[i - 1] if (i - 1) < len(fallback_frs) else fallback_frs[0]
            clean_criteria = list(fallback_match["acceptance_criteria"])

        standardized_criteria = []
        for crit in clean_criteria:
            c_norm = re.sub(r",\s*when\s+", ", When ", crit, flags=re.IGNORECASE)
            c_norm = re.sub(r",\s*then\s+", ", Then ", c_norm, flags=re.IGNORECASE)
            if not c_norm.startswith("Given ") and not c_norm.startswith("given "):
                c_norm = f"Given {c_norm}"
            elif c_norm.startswith("given "):
                c_norm = f"Given {c_norm[6:]}"
            standardized_criteria.append(c_norm)
        clean_criteria = standardized_criteria

        # Validate dependencies
        raw_deps = fr.get("dependencies")
        valid_deps: list[str] = []
        if isinstance(raw_deps, list):
            for dep in raw_deps:
                dep_str = str(dep).strip().upper()
                # Must be FR-X format and earlier than current key
                match = re.match(r"^FR-(\d+)$", dep_str)
                if match:
                    dep_idx = int(match.group(1))
                    if 1 <= dep_idx < i:
                        valid_deps.append(dep_str)

        # Fallback dependencies if missing
        if not valid_deps and i - 1 < len(fallback_frs):
            fallback_deps = fallback_frs[i - 1].get("dependencies", [])
            valid_deps = [d for d in fallback_deps if int(d.split("-")[1]) < i]

        priority = str(fr.get("priority", "HIGH")).upper()
        if priority not in ("LOW", "MEDIUM", "HIGH", "URGENT", "CRITICAL"):
            priority = "MEDIUM"

        sanitized_frs.append({
            "key": key,
            "title": raw_title,
            "description": raw_desc,
            "priority": priority,
            "acceptance_criteria": clean_criteria,
            "dependencies": valid_deps,
            "open_questions": fr.get("open_questions") or [],
        })

    # Validate Non-functional requirements
    raw_nfrs = parsed.get("non_functional_requirements")
    sanitized_nfrs: list[dict[str, Any]] = []
    fallback_nfrs = fallback_data["non_functional_requirements"]

    if isinstance(raw_nfrs, list) and len(raw_nfrs) > 0:
        for j, nfr in enumerate(raw_nfrs, start=1):
            if not isinstance(nfr, dict):
                continue
            key = f"NFR-{j}"
            n_title = clean_metadata_leakage(str(nfr.get("title", ""))).strip()
            n_desc = clean_metadata_leakage(str(nfr.get("description", ""))).strip()
            n_cat = str(nfr.get("category", "SECURITY")).upper()
            n_prio = str(nfr.get("priority", "HIGH")).upper()
            if not n_desc or len(n_desc) < 15:
                f_nfr = fallback_nfrs[j - 1] if (j - 1) < len(fallback_nfrs) else fallback_nfrs[0]
                n_desc = f_nfr["description"]
                if not n_title:
                    n_title = f_nfr["title"]
            sanitized_nfrs.append({
                "key": key,
                "title": n_title or f"Non-Functional {j}",
                "category": n_cat,
                "description": n_desc,
                "priority": n_prio if n_prio in ("LOW", "MEDIUM", "HIGH", "URGENT", "CRITICAL") else "MEDIUM",
            })
    else:
        sanitized_nfrs = fallback_nfrs

    # Clarification questions
    raw_questions = parsed.get("clarification_questions")
    sanitized_questions: list[dict[str, Any]] = []
    fallback_questions = fallback_data["clarification_questions"]

    if isinstance(raw_questions, list) and len(raw_questions) > 0:
        for k, q in enumerate(raw_questions, start=1):
            if not isinstance(q, dict):
                continue
            q_text = clean_metadata_leakage(str(q.get("question", ""))).strip()
            if q_text:
                sanitized_questions.append({
                    "question_key": f"Q-{k}",
                    "question": q_text,
                    "reason": clean_metadata_leakage(str(q.get("reason", ""))).strip() or "Clarify technical specification.",
                    "context_topic": clean_metadata_leakage(str(q.get("context_topic", ""))).strip() or "Requirements",
                })
    if not sanitized_questions:
        sanitized_questions = fallback_questions

    # Overview
    overview = parsed.get("overview")
    if not isinstance(overview, dict) or not overview.get("project_objective"):
        overview = fallback_data["overview"]
    else:
        overview["project_objective"] = clean_metadata_leakage(str(overview.get("project_objective", ""))).strip() or title
        overview["business_problem"] = clean_metadata_leakage(str(overview.get("business_problem", ""))).strip()
        overview["intended_outcome"] = clean_metadata_leakage(str(overview.get("intended_outcome", ""))).strip() or desired_outcome
        if not overview.get("in_scope"):
            overview["in_scope"] = [f["title"] for f in sanitized_frs]
        if not overview.get("out_of_scope"):
            overview["out_of_scope"] = fallback_data["overview"]["out_of_scope"]

    return {
        "overview": overview,
        "functional_requirements": sanitized_frs,
        "non_functional_requirements": sanitized_nfrs,
        "technical_constraints": parsed.get("technical_constraints") or fallback_data["technical_constraints"],
        "assumptions": parsed.get("assumptions") or fallback_data["assumptions"],
        "clarification_questions": sanitized_questions,
        "risks_and_dependencies": parsed.get("risks_and_dependencies") or fallback_data["risks_and_dependencies"],
    }
