// ── Open correct tab on load ───────────────────────────────────────────────────
// If the URL has ?tab=signup (e.g. from a "create account" link), open the signup tab immediately
const _tab = new URLSearchParams(window.location.search).get('tab');
if (_tab === 'signup') {
  switchTab('signup');
}

// ── Tab switching ──────────────────────────────────────────────────────────────
// Switches between the Sign In and Sign Up forms by toggling CSS classes.
// The sliding gold indicator under the tabs is moved via the 'right' class
function switchTab(tab) {
  const loginForm = document.getElementById('formLogin');
  const signupForm = document.getElementById('formSignup');
  const tabLogin = document.getElementById('tabLogin');
  const tabSignup = document.getElementById('tabSignup');
  const indicator = document.getElementById('tabIndicator');

  if (tab === 'login') {
    loginForm.classList.add('active');
    signupForm.classList.remove('active');
    tabLogin.classList.add('active');
    tabSignup.classList.remove('active');
    indicator.classList.remove('right');    // indicator slides to the left (login)
  } else {
    signupForm.classList.add('active');
    loginForm.classList.remove('active');
    tabSignup.classList.add('active');
    tabLogin.classList.remove('active');
    indicator.classList.add('right');       // indicator slides to the right (signup)
  }
  clearErrors();  // clear any validation errors when switching tabs
}


// ── Password visibility toggle ─────────────────────────────────────────────────
// Toggles the password input between 'password' (dots) and 'text' (visible), and swaps the eye icon
function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  const closed = btn.querySelector('.eye-closed');
  const open = btn.querySelector('.eye-open');

  if (input.type === 'password') {
    input.type = 'text';
    closed.style.display = 'none';
    open.style.display = 'block';
  } else {
    input.type = 'password';
    closed.style.display = 'block';
    open.style.display = 'none';
  }
}


// ── Validation helpers ─────────────────────────────────────────────────────────

// Marks an input as invalid — adds red border and shows error message below it
function setError(inputEl, errEl, msg) {
  inputEl.classList.add('error');
  inputEl.classList.remove('valid');
  errEl.textContent = msg;
}

// Marks an input as valid — adds green border and clears any error message
function setValid(inputEl, errEl) {
  inputEl.classList.remove('error');
  inputEl.classList.add('valid');
  errEl.textContent = '';
}

// Clears all validation state from every input and error element on the page
function clearErrors() {
  const inputs = document.querySelectorAll('input');
  for (let i = 0; i < inputs.length; i++) {
    inputs[i].classList.remove('error', 'valid');
  }
  const errorEls = document.querySelectorAll('.field-error');
  for (let i = 0; i < errorEls.length; i++) {
    errorEls[i].textContent = '';
  }
}

// Basic email format regex — just checks structure, not domain restrictions (server does that)
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;


// ── Password strength meter ────────────────────────────────────────────────────
// Scores the password on 5 criteria and updates the colored bar and label in real time
document.getElementById('signupPassword').addEventListener('input', function () {
  const val = this.value;
  const bar = document.getElementById('strengthBar');
  const fill = document.getElementById('strengthFill');
  const lbl = document.getElementById('strengthLabel');

  if (!val) {
    bar.classList.remove('visible');
    return;
  }
  bar.classList.add('visible');

  // Score 0-5 based on: length ≥8, length ≥12, mixed case, has digit, has special char
  let score = 0;
  if (val.length >= 8) {
    score++;
  }
  if (val.length >= 12) {
    score++;
  }
  if (/[A-Z]/.test(val) && /[a-z]/.test(val)) {
    score++;
  }
  if (/[0-9]/.test(val)) {
    score++;
  }
  if (/[^A-Za-z0-9]/.test(val)) {
    score++;
  }

  let pct = '';
  let color = '';
  let strengthText = '';
  if (score === 0) {
    pct = '20%'; color = '#d4614a'; strengthText = 'Weak';
  } else if (score === 1) {
    pct = '40%'; color = '#d4614a'; strengthText = 'Weak';
  } else if (score === 2) {
    pct = '60%'; color = '#c8a030'; strengthText = 'Fair';
  } else if (score === 3) {
    pct = '80%'; color = '#7aab58'; strengthText = 'Good';
  } else {
    pct = '100%'; color = '#5a9e6a'; strengthText = 'Strong';
  }
  fill.style.width = pct;
  fill.style.background = color;
  lbl.textContent = strengthText;
  lbl.style.color = color;
});


// ── Live field validation ──────────────────────────────────────────────────────

// Validates email format — server enforces university domain, this just checks basic structure
function validateEmail(inputEl, errEl) {
  const val = inputEl.value.trim();
  if (!val) {
    setError(inputEl, errEl, 'Email is required.');
    return false;
  }
  if (!emailRegex.test(val)) {
    setError(inputEl, errEl, 'Please enter a valid email address.');
    return false;
  }
  setValid(inputEl, errEl);
  return true;
}

// Validates password — minimum 8 characters (matches server-side rule)
function validatePassword(inputEl, errEl) {
  const val = inputEl.value;
  if (!val) {
    setError(inputEl, errEl, 'Password is required.');
    return false;
  }
  if (val.length < 8) {
    setError(inputEl, errEl, 'Password must be at least 8 characters.');
    return false;
  }
  setValid(inputEl, errEl);
  return true;
}

// Validates name — minimum 2 characters (matches server-side rule)
function validateName(inputEl, errEl) {
  const val = inputEl.value.trim();
  if (!val) {
    setError(inputEl, errEl, 'Name is required.');
    return false;
  }
  if (val.length < 2) {
    setError(inputEl, errEl, 'Please enter your full name.');
    return false;
  }
  setValid(inputEl, errEl);
  return true;
}


// ── Form submission validation ─────────────────────────────────────────────────

// Validates login form client-side before submitting. If valid, form submits naturally to Flask POST /login
document.getElementById('formLogin').addEventListener('submit', function (e) {
  const email = document.getElementById('loginEmail');
  const password = document.getElementById('loginPassword');
  const emailErr = document.getElementById('loginEmailErr');
  const passErr = document.getElementById('loginPasswordErr');

  const emailOk = validateEmail(email, emailErr);
  const passOk = validatePassword(password, passErr);

  if (!emailOk || !passOk) {
    e.preventDefault();  // block submission if any field fails
  }
});


// Validates signup form client-side before submitting. If valid, form submits naturally to Flask POST /register
document.getElementById('formSignup').addEventListener('submit', function (e) {
  const name = document.getElementById('signupName');
  const email = document.getElementById('signupEmail');
  const password = document.getElementById('signupPassword');
  const nameErr = document.getElementById('signupNameErr');
  const emailErr = document.getElementById('signupEmailErr');
  const passErr = document.getElementById('signupPasswordErr');

  const nameOk = validateName(name, nameErr);
  const emailOk = validateEmail(email, emailErr);
  const passOk = validatePassword(password, passErr);

  if (!nameOk || !emailOk || !passOk) {
    e.preventDefault();  // block submission if any field fails
  }
});


// ── Tab + eye button wiring ────────────────────────────────────────────────────

document.getElementById('tabLogin').addEventListener('click', () => switchTab('login'));
document.getElementById('tabSignup').addEventListener('click', () => switchTab('signup'));
document.getElementById('switchToSignup').addEventListener('click', () => switchTab('signup'));
document.getElementById('switchToLogin').addEventListener('click', () => switchTab('login'));

// Wire up all eye buttons (show/hide password toggle)
const eyeBtns = document.querySelectorAll('.eye-btn');
for (let i = 0; i < eyeBtns.length; i++) {
  eyeBtns[i].addEventListener('click', () => togglePassword(eyeBtns[i].dataset.target, eyeBtns[i]));
}

// ── Blur-time validation ───────────────────────────────────────────────────────
// Validates each field when the user leaves it (on blur), giving immediate feedback
document.getElementById('loginEmail').addEventListener('blur', function () {
  validateEmail(this, document.getElementById('loginEmailErr'));
});
document.getElementById('loginPassword').addEventListener('blur', function () {
  validatePassword(this, document.getElementById('loginPasswordErr'));
});
document.getElementById('signupName').addEventListener('blur', function () {
  validateName(this, document.getElementById('signupNameErr'));
});
document.getElementById('signupEmail').addEventListener('blur', function () {
  validateEmail(this, document.getElementById('signupEmailErr'));
});
document.getElementById('signupPassword').addEventListener('blur', function () {
  validatePassword(this, document.getElementById('signupPasswordErr'));
});
