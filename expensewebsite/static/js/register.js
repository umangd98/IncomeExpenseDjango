const usernameField = document.querySelector('#usernameField');
const feedbackField = document.querySelector('.UsernamefeedbackField');
const emailField = document.querySelector('#emailField');
const EmailfeedbackField = document.querySelector('.EmailfeedbackField');
const usernameSuccessOutput = document.querySelector('.usernameSuccessOutput');
const passwordField = document.querySelector('#passwordField');
const showPasswordToggle = document.querySelector('.showPasswordToggle');
const submitBtn = document.querySelector('.submit-btn');

const handleToggleInput = (e) => {
  if (showPasswordToggle.textContent === 'SHOW') {
    showPasswordToggle.textContent = 'HIDE';
    passwordField.setAttribute('type', 'text');
  } else {
    showPasswordToggle.textContent = 'SHOW';
    passwordField.setAttribute('type', 'password');
  }
};
showPasswordToggle.addEventListener('click', handleToggleInput);

emailField.addEventListener('keyup', (e) => {
  const emailVal = e.target.value;
  emailField.classList.remove('is-invalid');
  EmailfeedbackField.style.display = 'none';
  console.log(emailVal);
  if (emailVal.length > 0) {
    fetch('/authentication/validate-email', {
      body: JSON.stringify({ email: emailVal }),
      method: 'POST',
    })
      .then((res) => res.json())
      .then((data) => {
        console.log('data', data);
        if (data.email_error) {
          submitBtn.disabled = true;
          emailField.classList.add('is-invalid');
          EmailfeedbackField.innerHTML = `<p>${data.email_error}</p>`;
          EmailfeedbackField.style.display = 'block';
        } else {
          submitBtn.removeAttribute('disabled');
        }
      });
  }
});
usernameField.addEventListener('keyup', (e) => {
  const usernameVal = e.target.value;
  usernameSuccessOutput.style.display = 'block';

  usernameSuccessOutput.textContent = `Checking ${usernameVal}`;

  usernameField.classList.remove('is-invalid');
  feedbackField.style.display = 'none';
  console.log(usernameVal);
  if (usernameVal.length > 0) {
    fetch('/authentication/validate-username', {
      body: JSON.stringify({ username: usernameVal }),
      method: 'POST',
    })
      .then((res) => res.json())
      .then((data) => {
        console.log('data', data);
        usernameSuccessOutput.style.display = 'none';
        if (data.username_error) {
          emailField.classList.add('is-invalid');
          usernameField.classList.add('is-invalid');
          feedbackField.innerHTML = `<p>${data.username_error}</p>`;
          feedbackField.style.display = 'block';
          submitBtn.disabled = true;
        } else {
          submitBtn.removeAttribute('disabled');
        }
      });
  }
});
