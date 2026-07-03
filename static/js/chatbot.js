// EcoEats Floating AI Chatbot JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 20 Questions and Answers Database
    const chatbotDatabase = [
        {
            id: 1,
            question: "What is EcoEats?",
            keywords: ["what is", "about", "ecoeats", "eco eats", "definition", "purpose", "mission"],
            answer: "<p><strong>EcoEats</strong> is a professional food waste redistribution platform designed to bridge the gap between surplus food generators and organizations/individuals in need.</p><p>Our mission is to minimize environmental waste and support local communities by facilitating direct food donations.</p>"
        },
        {
            id: 2,
            question: "How does the food donation lifecycle work?",
            keywords: ["lifecycle", "how does it work", "flow", "process", "steps", "working", "donation lifecycle"],
            answer: "<p>The EcoEats donation lifecycle works in 6 simple steps:</p><ol><li><strong>Listing:</strong> A Donor creates a food listing with quantity, expiry, and coordinates.</li><li><strong>Browsing:</strong> Receivers browse active food listings near them.</li><li><strong>Requesting:</strong> A Receiver submits a request with pickup details.</li><li><strong>Approval:</strong> The Donor reviews and approves the request.</li><li><strong>Coordination:</strong> Both parties chat in real-time to finalize logistics.</li><li><strong>Completion & Feedback:</strong> The Donor marks the request as completed, and the Receiver rates the experience.</li></ol>"
        },
        {
            id: 3,
            question: "Who can register on EcoEats?",
            keywords: ["register", "sign up", "who can use", "membership", "roles", "join", "eligibility"],
            answer: "<p>Anyone looking to reduce food waste can register! We support two primary roles:</p><ul><li><strong>Donors:</strong> Restaurants, grocery stores, hotels, wedding caterers, or individuals with surplus food.</li><li><strong>Receivers:</strong> NGOs, community shelters, food banks, soup kitchens, or individuals seeking assistance.</li></ul>"
        },
        {
            id: 4,
            question: "How do I sign up as a Donor?",
            keywords: ["sign up donor", "become donor", "donor registration", "register donor", "create donor"],
            answer: "<p>To sign up as a Donor:</p><ol><li>Click on <strong>Register</strong> in the top navigation bar.</li><li>Create your basic account.</li><li>On the <strong>Profile Creation</strong> screen, select your role as <strong>Donor</strong>.</li><li>Provide your business or individual details, contact number, and base location coordinates.</li></ol>"
        },
        {
            id: 5,
            question: "How do I sign up as a Receiver?",
            keywords: ["sign up receiver", "become receiver", "receiver registration", "register receiver", "create receiver"],
            answer: "<p>To sign up as a Receiver:</p><ol><li>Click on <strong>Register</strong> in the top navigation bar and create an account.</li><li>On the <strong>Profile Creation</strong> screen, select <strong>Receiver</strong>.</li><li>Provide your contact information, location, and upload organization verification documents (like license PDFs) to establish trust.</li></ol>"
        },
        {
            id: 6,
            question: "How do I add a new food listing?",
            keywords: ["add food", "create listing", "list food", "donate food", "new listing", "post food"],
            answer: "<p>If you are a registered Donor:</p><ol><li>Log in and navigate to your <strong>Donor Dashboard</strong>.</li><li>Click the <strong>Add Food</strong> button.</li><li>Fill out the form: food name, description, category (vegetarian/non-vegetarian), quantity, preparation/expiry time, and physical coordinates.</li><li>Click <strong>Submit</strong>. It is now instantly visible to receivers!</li></ol>"
        },
        {
            id: 7,
            question: "How do I find and request food listings?",
            keywords: ["find food", "request food", "browse listings", "get food", "order food", "pickup request"],
            answer: "<p>If you are a registered Receiver:</p><ol><li>Log in and view your <strong>Receiver Dashboard</strong> to see available food listings.</li><li>Click on any listing card to view details (donor info, expiry, coordinates, map).</li><li>Click <strong>Request Food</strong>.</li><li>Fill in estimated pickup time, vehicle info, and contact person, then submit.</li></ol>"
        },
        {
            id: 8,
            question: "Is there any fee or cost to use EcoEats?",
            keywords: ["fee", "cost", "price", "free", "charge", "payment", "subscription"],
            answer: "<p>No! EcoEats is <strong>100% free</strong> to use for both Donors and Receivers.</p><p>We are a community-driven initiative focused on sustainability and food security, so we do not charge any registration fees, listing fees, or transaction costs.</p>"
        },
        {
            id: 9,
            question: "How do we ensure food safety?",
            keywords: ["safety", "spoiled", "hygiene", "food quality", "quality assurance", "expiration", "safe"],
            answer: "<p>Food safety is crucial. We maintain it through:</p><ul><li><strong>Expiry Tracking:</strong> Donors must provide a clear preparation time and expiry date/time. Expired listings are hidden automatically.</li><li><strong>Inspections:</strong> Receivers should check the food visually and smell it upon pickup.</li><li><strong>Disputes:</strong> If food is unsafe or spoiled, receivers can use the <strong>Report</strong> feature to flag it for Admin review.</li></ul>"
        },
        {
            id: 10,
            question: "How does the map/location feature work?",
            keywords: ["map", "location", "coordinates", "gps", "distance", "latitude", "longitude", "leaflet"],
            answer: "<p>EcoEats captures exact coordinates (latitude and longitude) during profile registration and food listing creation.</p><p>On the food detail page, a map (powered by Leaflet/OpenStreetMap) renders the precise pickup point, helping receivers find the donor and coordinate logistics easily.</p>"
        },
        {
            id: 11,
            question: "How do Donors and Receivers coordinate?",
            keywords: ["chat", "message", "communicate", "contact", "talk to donor", "talk to receiver", "inbox"],
            answer: "<p>Communication is simplified through our built-in <strong>Chat System</strong>.</p><p>Once a Receiver requests a listing, a dedicated conversation opens. Both parties can exchange real-time text messages and upload photos of the food/pickup location to align on coordinates and time.</p>"
        },
        {
            id: 12,
            question: "What should I do if a pickup is complete?",
            keywords: ["complete pickup", "mark complete", "pickup completed", "handover", "finish request"],
            answer: "<p>Once food is handed over physically, the Donor should navigate to 'Manage Food' on their dashboard and click <strong>Mark Completed</strong> on the request.</p><p>This closes the listing and allows the Receiver to submit ratings and feedback.</p>"
        },
        {
            id: 13,
            question: "How does the rating and feedback system work?",
            keywords: ["rating", "feedback", "review", "stars", "dispute", "score", "trust score"],
            answer: "<p>After a request is marked as completed:</p><ul><li>The Receiver receives a prompt to rate the experience from <strong>1 to 5 stars</strong> and write a review.</li><li>If the transaction had issues (e.g. food was not as described), they can submit a formal **dispute report** to the administrator.</li></ul>"
        },
        {
            id: 14,
            question: "How are organizations verified?",
            keywords: ["verification", "verify", "badge", "license", "government document", "ngo certificate", "trust"],
            answer: "<p>To build trust and prevent fraud, organizations can upload verification files (like food safety licenses or NGO registrations) in PDF format during registration.</p><p>System Admins manually review these files and award a green <strong>Verified</strong> badge visible on their profiles.</p>"
        },
        {
            id: 15,
            question: "What can the Admin see and moderate?",
            keywords: ["admin", "moderator", "ban", "unban", "moderation", "admin panel", "reports", "logs"],
            answer: "<p>Admins have global oversight through the <strong>Admin Dashboard</strong>, which includes:</p><ul><li><strong>User Management:</strong> Verify organization profiles, promote users, or ban/unban rule-breaking accounts.</li><li><strong>Content Moderation:</strong> Delete inappropriate listings or resolve dispute reports.</li><li><strong>System Logs:</strong> View system-wide activity logs to ensure platform integrity.</li></ul>"
        },
        {
            id: 16,
            question: "How do I contact support or submit inquiries?",
            keywords: ["support", "contact sales", "contact support", "help desk", "email", "inquiry", "sales"],
            answer: "<p>For business inquiries, partnerships, or support requests, you can visit our <strong>Contact Sales</strong> page in the top nav bar.</p><p>Fill out the form with your name, organization, email, and inquiry size. Our support team will get back to you via email shortly.</p>"
        },
        {
            id: 17,
            question: "Can I edit or delete my food listing?",
            keywords: ["edit listing", "delete listing", "remove food", "cancel food", "modify food"],
            answer: "<p>Yes! Donors have full control over their listings. Go to the <strong>Manage Food</strong> page on the Donor Dashboard. From there, you can:</p><ul><li><strong>Delete:</strong> Completely remove the listing.</li><li><strong>Mark Expired:</strong> Manually archive the listing if food goes bad or is distributed offline.</li></ul>"
        },
        {
            id: 18,
            question: "Can I trace my previous donations or pickups?",
            keywords: ["history", "previous donations", "past requests", "trace", "analytics", "records"],
            answer: "<p>Yes! Both Donors and Receivers have a history section on their dashboards.</p><p>You can view all past listings, requests, pickup dates, and completion statuses to keep track of your active participation and social contribution.</p>"
        },
        {
            id: 19,
            question: "What if the food listing is expired?",
            keywords: ["expired food", "expiration date", "old listing", "expired listings", "past expiry"],
            answer: "<p>Food safety is essential, so EcoEats automatically hides listings from the active feed once their expiry time passes.</p><p>Donors are also encouraged to manually expire listings early if the food quality begins to degrade before the scheduled expiry time.</p>"
        },
        {
            id: 20,
            question: "Can individuals donate food, or only organizations?",
            keywords: ["individual", "single person", "household", "home cook", "business only", "ngo only", "anyone"],
            answer: "<p>Both! Individuals and large organizations are equally welcome to list surplus food on EcoEats.</p><p>Whether you have leftover food from a family gathering or a massive excess from a hotel banquet, you can list it here to help reduce local food waste.</p>"
        }
    ];

    // Select DOM elements
    const fabButton = document.getElementById('ecoChatbotFab');
    const chatbotWindow = document.getElementById('ecoChatbotWindow');
    const closeButton = document.getElementById('ecoChatbotClose');
    const chatBody = document.getElementById('ecoChatbotBody');
    const chatInput = document.getElementById('ecoChatbotInput');
    const sendButton = document.getElementById('ecoChatbotSend');
    const chipsContainer = document.getElementById('ecoChatbotChips');
    const notificationBadge = document.getElementById('ecoChatbotBadge');

    let hasGreeted = false;

    // Toggle Chat Window
    function toggleChat() {
        const isActive = chatbotWindow.classList.contains('active');
        if (isActive) {
            chatbotWindow.classList.remove('active');
            fabButton.classList.remove('active');
        } else {
            chatbotWindow.classList.add('active');
            fabButton.classList.add('active');
            // Hide notification badge when opened
            if (notificationBadge) {
                notificationBadge.style.display = 'none';
            }
            // Trigger welcome greeting if not done already
            if (!hasGreeted) {
                triggerGreeting();
            }
        }
    }

    fabButton.addEventListener('click', toggleChat);
    closeButton.addEventListener('click', toggleChat);

    // Initial greeting trigger with styling delay
    function triggerGreeting() {
        hasGreeted = true;
        showTypingIndicator();
        setTimeout(function() {
            hideTypingIndicator();
            appendMessage("bot", "<p>Hi there! 👋 Welcome to the <strong>EcoEats Support Assistant</strong>.</p><p>I am here to answer your questions about the EcoEats platform. Feel free to select a popular topic below, or type your own question in the box below!</p>");
            renderQuickReplies();
        }, 1200);
    }

    // Render Quick Replies Chips
    function renderQuickReplies() {
        chipsContainer.innerHTML = '';
        chatbotDatabase.forEach(item => {
            const chip = document.createElement('div');
            chip.className = 'eco-chatbot-chip';
            chip.innerText = item.question;
            chip.addEventListener('click', () => handleQuestionSelect(item));
            chipsContainer.appendChild(chip);
        });
    }

    // Handle Quick Reply Choice
    function handleQuestionSelect(item) {
        // Append user question
        appendMessage("user", item.question);
        
        // Show typing indicator
        showTypingIndicator();

        // Delay response to look organic
        setTimeout(function() {
            hideTypingIndicator();
            appendMessage("bot", item.answer);
        }, 1000);
    }

    // Show/Hide Typing Indicator
    function showTypingIndicator() {
        // Prevent duplicate indicator
        if (document.getElementById('ecoChatbotTypingIndicator')) return;

        const indicator = document.createElement('div');
        indicator.id = 'ecoChatbotTypingIndicator';
        indicator.className = 'eco-chatbot-typing';
        indicator.innerHTML = `
            <div class="eco-chatbot-dot"></div>
            <div class="eco-chatbot-dot"></div>
            <div class="eco-chatbot-dot"></div>
        `;
        chatBody.appendChild(indicator);
        scrollToBottom();
    }

    function hideTypingIndicator() {
        const indicator = document.getElementById('ecoChatbotTypingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    // Append message to Chat body
    function appendMessage(sender, content) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `eco-chatbot-msg eco-chatbot-msg-${sender}`;
        msgDiv.innerHTML = content;
        chatBody.appendChild(msgDiv);
        scrollToBottom();
    }

    // Scroll to bottom of chat body
    function scrollToBottom() {
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    // Match input against DB keywords
    function findBestMatch(userText) {
        const text = userText.toLowerCase().trim();
        if (!text) return null;

        let bestItem = null;
        let highestScore = 0;

        // Simple scoring algorithm based on matching keywords
        chatbotDatabase.forEach(item => {
            let score = 0;
            // Check for keyword matches
            item.keywords.forEach(keyword => {
                if (text.includes(keyword)) {
                    score += 2;
                }
            });

            // Check if user text contains question text
            const cleanQuestion = item.question.toLowerCase();
            if (cleanQuestion.includes(text) || text.includes(cleanQuestion)) {
                score += 5;
            }

            // Score based on word overlap
            const userWords = text.split(/\s+/);
            const questionWords = cleanQuestion.split(/\s+/);
            userWords.forEach(word => {
                if (word.length > 3 && questionWords.includes(word)) {
                    score += 1;
                }
            });

            if (score > highestScore) {
                highestScore = score;
                bestItem = item;
            }
        });

        // Threshold to prevent matching random unrelated words
        return highestScore >= 2 ? bestItem : null;
    }

    // Handle user input submit
    function handleSend() {
        const text = chatInput.value.trim();
        if (!text) return;

        chatInput.value = '';
        appendMessage("user", text);

        showTypingIndicator();

        setTimeout(function() {
            hideTypingIndicator();
            const match = findBestMatch(text);
            if (match) {
                appendMessage("bot", match.answer);
            } else {
                appendMessage("bot", `<p>I couldn't quite find an answer for that. Here are some options:</p><ul><li>Try choosing one of the popular topics in the scrollable chips below.</li><li>Check our comprehensive <a href="/faqs/">FAQs Page</a>.</li><li>Submit a question via our <a href="/contact-sales/">Contact Page</a> to reach an admin.</li></ul>`);
            }
        }, 1200);
    }

    // Listeners for input
    sendButton.addEventListener('click', handleSend);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleSend();
        }
    });

    // Make the chat badge blink/pulse a few times initially on load to draw attention
    setTimeout(() => {
        if (notificationBadge && !chatbotWindow.classList.contains('active')) {
            notificationBadge.style.display = 'block';
        }
    }, 2000);
});
