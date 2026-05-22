/* ── Tab switching ─────────────────────────────────────────── */
function switchTab(tab) {
  const loginForm  = document.getElementById('formLogin');
  const signupForm = document.getElementById('formSignup');
  const tabLogin   = document.getElementById('tabLogin');
  const tabSignup  = document.getElementById('tabSignup');
  const indicator  = document.getElementById('tabIndicator');

  if (tab === 'login') {
    loginForm.classList.add('active');
    signupForm.classList.remove('active');
    tabLogin.classList.add('active');
    tabSignup.classList.remove('active');
    indicator.classList.remove('right');
  } else {
    signupForm.classList.add('active');
    loginForm.classList.remove('active');
    tabSignup.classList.add('active');
    tabLogin.classList.remove('active');
    indicator.classList.add('right');
  }
  clearErrors();
}


/* ── Password visibility toggle ────────────────────────────── */
function togglePassword(inputId, btn) {
  const input  = document.getElementById(inputId);
  const closed = btn.querySelector('.eye-closed');
  const open   = btn.querySelector('.eye-open');

  if (input.type === 'password') {
    input.type = 'text';
    closed.style.display = 'none';
    open.style.display   = 'block';
  } else {
    input.type = 'password';
    closed.style.display = 'block';
    open.style.display   = 'none';
  }
}


/* ── Helpers ────────────────────────────────────────────────── */
function setError(inputEl, errEl, msg) {
  inputEl.classList.add('error');
  inputEl.classList.remove('valid');
  errEl.textContent = msg;
}

function setValid(inputEl, errEl) {
  inputEl.classList.remove('error');
  inputEl.classList.add('valid');
  errEl.textContent = '';
}

function clearErrors() {
  document.querySelectorAll('input').forEach(i => {
    i.classList.remove('error', 'valid');
  });
  document.querySelectorAll('.field-error').forEach(e => e.textContent = '');
}

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;


/* ── Password strength ──────────────────────────────────────── */
document.getElementById('signupPassword').addEventListener('input', function () {
  const val      = this.value;
  const bar      = document.getElementById('strengthBar');
  const fill     = document.getElementById('strengthFill');
  const lbl      = document.getElementById('strengthLabel');

  if (!val) { bar.classList.remove('visible'); return; }
  bar.classList.add('visible');

  let score = 0;
  if (val.length >= 8)  score++;
  if (val.length >= 12) score++;
  if (/[A-Z]/.test(val) && /[a-z]/.test(val)) score++;
  if (/[0-9]/.test(val))  score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;

  const levels = [
    { pct: '20%', color: '#d4614a', text: 'Weak'   },
    { pct: '40%', color: '#d4614a', text: 'Weak'   },
    { pct: '60%', color: '#c8a030', text: 'Fair'   },
    { pct: '80%', color: '#7aab58', text: 'Good'   },
    { pct: '100%',color: '#5a9e6a', text: 'Strong' },
  ];
  const l = levels[Math.min(score, 4)];
  fill.style.width      = l.pct;
  fill.style.background = l.color;
  lbl.textContent       = l.text;
  lbl.style.color       = l.color;
});


/* ── Live validation ────────────────────────────────────────── */
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


/* ── Login form submission ─────────────────────────────────── */
document.getElementById('formLogin').addEventListener('submit', function (e) {
  const email    = document.getElementById('loginEmail');
  const password = document.getElementById('loginPassword');
  const emailErr = document.getElementById('loginEmailErr');
  const passErr  = document.getElementById('loginPasswordErr');

  const emailOk = validateEmail(email, emailErr);
  const passOk  = validatePassword(password, passErr);

  if (!emailOk || !passOk) {
    e.preventDefault();
  }
  // if valid, form submits naturally to Flask POST /login
});


/* ── Signup form submission ────────────────────────────────── */
document.getElementById('formSignup').addEventListener('submit', function (e) {
  const name     = document.getElementById('signupName');
  const email    = document.getElementById('signupEmail');
  const password = document.getElementById('signupPassword');
  const nameErr  = document.getElementById('signupNameErr');
  const emailErr = document.getElementById('signupEmailErr');
  const passErr  = document.getElementById('signupPasswordErr');

  const nameOk  = validateName(name, nameErr);
  const emailOk = validateEmail(email, emailErr);
  const passOk  = validatePassword(password, passErr);

  if (!nameOk || !emailOk || !passOk) {
    e.preventDefault();
  }
  // if valid, form submits naturally to Flask POST /register
});


/* ── Blur-time validation (validate as user leaves each field) ─ */
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
