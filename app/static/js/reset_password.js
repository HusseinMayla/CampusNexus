// Password visibility toggle function (needs to be global since it is called inline via onclick)
function toggleFieldPassword(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const closed = btn.querySelector('.eye-closed');
  const open = btn.querySelector('.eye-open');

  if (input.type === 'password') {
    input.type = 'text';
    if (closed) closed.style.display = 'none';
    if (open) open.style.display = 'block';
  } else {
    input.type = 'password';
    if (closed) closed.style.display = 'block';
    if (open) open.style.display = 'none';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Password strength calculations
  const passwordInput = document.getElementById('resetPassword');
  if (passwordInput) {
    passwordInput.addEventListener('input', function () {
      const val = this.value;
      const bar = document.getElementById('strengthBar');
      const fill = document.getElementById('strengthFill');
      const lbl = document.getElementById('strengthLabel');

      if (!bar) return;

      if (!val) {
        bar.classList.remove('visible');
        return;
      }
      bar.classList.add('visible');

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

      const levels = [
        { pct: '20%', color: '#d4614a', text: 'Weak'   },
        { pct: '40%', color: '#d4614a', text: 'Weak'   },
        { pct: '60%', color: '#c8a030', text: 'Fair'   },
        { pct: '80%', color: '#7aab58', text: 'Good'   },
        { pct: '100%',color: '#5a9e6a', text: 'Strong' },
      ];
      const l = levels[Math.min(score, 4)];
      if (fill) {
        fill.style.width = l.pct;
        fill.style.background = l.color;
      }
      if (lbl) {
        lbl.textContent = l.text;
        lbl.style.color = l.color;
      }
    });
  }

  // Submit checks
  const form = document.getElementById('formReset');
  const confirmInput = document.getElementById('confirmPassword');
  const passErr = document.getElementById('resetPasswordErr');
  const confirmErr = document.getElementById('confirmPasswordErr');

  if (form && passwordInput && confirmInput && passErr && confirmErr) {
    form.addEventListener('submit', (e) => {
      let valid = true;
      passErr.textContent = '';
      confirmErr.textContent = '';
      passwordInput.classList.remove('error');
      confirmInput.classList.remove('error');

      const passVal = passwordInput.value;
      const confirmVal = confirmInput.value;

      if (!passVal) {
        passErr.textContent = 'Password is required.';
        passwordInput.classList.add('error');
        valid = false;
      } else if (passVal.length < 8) {
        passErr.textContent = 'Password must be at least 8 characters.';
        passwordInput.classList.add('error');
        valid = false;
      }

      if (!confirmVal) {
        confirmErr.textContent = 'Please confirm your password.';
        confirmInput.classList.add('error');
        valid = false;
      } else if (passVal !== confirmVal) {
        confirmErr.textContent = 'Passwords do not match.';
        confirmInput.classList.add('error');
        valid = false;
      }

      if (!valid) {
        e.preventDefault();
      }
    });
  }
});
