document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM fully loaded and parsed');

    // Redirect to the main page (index.html) from the first page
    const startButton = document.getElementById('startButton');
    console.log('startButton:', startButton);
    if (startButton) {
        startButton.addEventListener('click', function () {
            console.log('Redirecting to index page...');
            showLoadingSpinner();
            window.location.href = '/index';
        });
    }

    // Handle email form submission
    const emailForm = document.getElementById('emailForm');
    console.log('emailForm:', emailForm);
    if (emailForm) {
        emailForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const emailElement = document.getElementById('email');
            console.log('emailElement:', emailElement);
            if (emailElement) {
                const email = emailElement.value;
                console.log('Email:', email);
                // Save email to sessionStorage for later use
                sessionStorage.setItem('userEmail', email);
                fetch('/submit_email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email }),
                })
                .then((response) => {
                    if (response.ok) return response.json();
                    else throw new Error('Email not found');
                })
                .then((data) => {
                    console.log('Email verified:', data.message);
                    const welcomeMessage = document.getElementById('welcomeMessage');
                    welcomeMessage.innerHTML = `<span class="welcome-text">Hello ${data.name} &#128522;</span>`;
                    const viewRulesButton = document.getElementById('viewRulesButton');
                    console.log('viewRulesButton:', viewRulesButton);
                    if (viewRulesButton) {
                        viewRulesButton.style.display = 'block';
                    }
                })
                .catch((error) => {
                    console.error('Error:', error);
                    document.getElementById('welcomeMessage').innerText = 'Email not found. Please try again.';
                });
            } else {
                console.error('Email input element not found.');
            }
        });
    }

    // Timer function
    function startTimer(duration) {
        let timer = duration, minutes, seconds;
        const intervalId = setInterval(function () {
            minutes = parseInt(timer / 60, 10);
            seconds = parseInt(timer % 60, 10);
            document.getElementById('timer').textContent = `Time left: ${minutes}:${seconds}`;
            if (--timer < 0) {
                clearInterval(intervalId);
                const submitButton = document.getElementById('submitButton');
                console.log('submitButton:', submitButton);
                if (submitButton) {
                    submitButton.click();
                }
            }
        }, 1000);
    }

    // Fetch and display questions (for questions page only)
    const examSection = document.getElementById('examSection');
    console.log('examSection:', examSection);
    if (examSection) {
        console.log('Fetching questions...');
        fetch('/questions')
            .then((response) => response.json())
            .then((questions) => {
                console.log('Questions fetched:', questions);
                displayQuestions(questions);
                startTimer(40 * 60); // Start a 40-minute timer
            })
            .catch((error) => console.error('Error fetching questions:', error));
    }

    // Display questions on the page with numbering
    function displayQuestions(questions) {
        const examSection = document.getElementById('examSection');
        const progressBar = document.getElementById('progressBar');
        console.log('examSection:', examSection);
        if (!examSection) {
            console.error('Exam section not found.');
            return;
        }
        examSection.innerHTML = ''; // Clear previous content
        const totalQuestions = Object.keys(questions).length;
        let answeredQuestions = 0;

        Object.keys(questions).forEach((q_id) => {
            const question = questions[q_id];
            const questionDiv = document.createElement('div');
            questionDiv.classList.add('question-box');
            questionDiv.innerHTML = `<p>${q_id}. ${question.question}</p>`; // Add question number
            question.options.forEach((option) => {
                const optionDiv = document.createElement('div');
                optionDiv.classList.add('question-options');
                optionDiv.innerHTML = ` <input type="radio" name="question-${q_id}" value="${option[0]}"> <label>${option}</label> `;
                optionDiv.querySelector('input').addEventListener('change', function() {
                    answeredQuestions++;
                    updateProgressBar();
                });
                questionDiv.appendChild(optionDiv);
            });
            examSection.appendChild(questionDiv);
        });

        const submitButton = document.createElement('button');
        submitButton.id = 'submitButton';
        submitButton.textContent = 'Submit';
        examSection.appendChild(submitButton);
        submitButton.addEventListener('click', function () {
            const answers = collectAnswers();
            // Get email and full name from sessionStorage
            const email = sessionStorage.getItem('userEmail');
            const fullName = sessionStorage.getItem('fullName');
            console.log('Email:', email, 'Full Name:', fullName);
            if (email && fullName) {
                fetch('/submit_exam', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ answers: answers, email: email, full_name: fullName }),
                })
                .then((response) => response.json())
                .then((data) => {
                    displayResults(data);
                    triggerConfetti(); // Trigger confetti celebration
                })
                .catch((error) => console.error('Error submitting exam:', error));
            } else {
                console.error('Email or full name not found or empty.');
            }
        });

        // Update progress bar
        function updateProgressBar() {
            const progress = (answeredQuestions / totalQuestions) * 100;
            progressBar.style.width = `${progress}%`;
            progressBar.textContent = `${Math.round(progress)}%`;
        }

        // Collect answers from the form
        function collectAnswers() {
            const answers = {};
            const questionElements = document.querySelectorAll('[name^="question-"]');
            questionElements.forEach((el) => {
                if (el.checked) {
                    const q_id = el.name.split('-')[1];
                    answers[q_id] = el.value;
                }
            });
            console.log('Collected answers:', answers);
            return answers;
        }
    }

    // Display results on the page
    function displayResults(data) {
        const resultSection = document.getElementById('resultSection');
        console.log('resultSection:', resultSection);
        if (!resultSection) {
            console.error('Result section not found.');
            return;
        }
        const userName = data.full_name; // Get the user's full name from the data
        resultSection.innerHTML = `
            <h2>Thank you for appearing for the examination, ${userName}!</h2>
            <p class="result-subtext">Please find your result below. 😊</p>
            <div class="result-box">
                <p>Your score: ${data.score}</p>
                <p>Correct answers: ${data.correct_count}</p>
                <p>Wrong answers: ${data.wrong_count}</p>
            </div>
        `;
        const examSection = document.getElementById('examSection');
        if (examSection) {
            examSection.style.display = 'none';
        }
    }

    // Trigger confetti celebration
    function triggerConfetti() {
        const duration = 2 * 1000; // 2 seconds
        const end = Date.now() + duration;

        (function frame() {
            confetti({
                particleCount: 5,
                angle: 60,
                spread: 55,
                origin: { x: 0 }
            });
            confetti({
                particleCount: 5,
                angle: 120,
                spread: 55,
                origin: { x: 1 }
            });

            if (Date.now() < end) {
                requestAnimationFrame(frame);
            }
        }());
    }

    // Show loading spinner
    function showLoadingSpinner() {
        const loadingSpinner = document.getElementById('loadingSpinner');
        console.log('loadingSpinner:', loadingSpinner);
        if (loadingSpinner) {
            loadingSpinner.style.display = 'block';
        }
    }

    // Hide loading spinner
    function hideLoadingSpinner() {
        const loadingSpinner = document.getElementById('loadingSpinner');
        console.log('loadingSpinner:', loadingSpinner);
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
    }
    // Modal Popup for Rules
    const modal = document.getElementById('rulesModal');
    const btn = document.getElementById('viewRulesButton');
    const span = document.getElementsByClassName('close')[0];
    const rulesCheckbox = document.getElementById('rulesCheckbox');
    const fullNameInput = document.getElementById('fullName');
    const confirmRulesButton = document.getElementById('confirmRulesButton');
    console.log('modal:', modal);
    console.log('btn:', btn);
    console.log('span:', span);
    console.log('rulesCheckbox:', rulesCheckbox);
    console.log('fullNameInput:', fullNameInput);
    console.log('confirmRulesButton:', confirmRulesButton);
    if (btn && modal && span && rulesCheckbox && fullNameInput && confirmRulesButton) {
        btn.onclick = function() {
            modal.style.display = 'block';
        }
        span.onclick = function() {
            modal.style.display = 'none';
        }
        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
        // Enable confirm button only if checkbox is checked and full name is provided
        rulesCheckbox.addEventListener('change', function() {
            confirmRulesButton.disabled = !(rulesCheckbox.checked && fullNameInput.value.trim() !== '');
        });
        fullNameInput.addEventListener('input', function() {
            confirmRulesButton.disabled = !(rulesCheckbox.checked && fullNameInput.value.trim() !== '');
        });
        confirmRulesButton.addEventListener('click', function() {
            modal.style.display = 'none';
            const startExamButton = document.getElementById('startButton');
            console.log('startExamButton:', startExamButton);
            if (startExamButton) {
                startExamButton.style.display = 'block';
                startExamButton.addEventListener('click', function () {
                    console.log('Redirecting to questions page...');
                    showLoadingSpinner();
                    window.location.href = '/questions_page';
                    startTimer(40 * 60); // Start a 40-minute timer
                });
            }
            // Save full name to sessionStorage for later use
            const fullName = fullNameInput.value.trim();
            sessionStorage.setItem('fullName', fullName);
        });
    } else {
        console.error('One or more elements for the rules modal are not found in the DOM.');
    }
});