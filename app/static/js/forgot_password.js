// Simple client-side validation for forgot password
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('formForgot');
  const emailInput = document.getElementById('forgotEmail');
  const emailErr = document.getElementById('forgotEmailErr');

  if (form && emailInput && emailErr) {
    form.addEventListener('submit', (e) => {
      let valid = true;
      emailErr.textContent = '';
      emailInput.classList.remove('error');

      const emailVal = emailInput.value.trim();
      if (!emailVal) {
        emailErr.textContent = 'Email address is required.';
        emailInput.classList.add('error');
        valid = false;
      } else if (!/^[^\s@]+@[^\s@]+\.[edu|ac]+.*$/i.test(emailVal)) {
        emailErr.textContent = 'Please use a university email address (.edu or .ac.xx).';
        emailInput.classList.add('error');
        valid = false;
      }

      if (!valid) {
        e.preventDefault();
      }
    });
  }
});
