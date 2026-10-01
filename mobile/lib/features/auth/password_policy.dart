const int minimumNewPasswordLength = 10;

bool loginPasswordLooksValid(String password) => password.isNotEmpty;

bool newPasswordLooksValid(String password) =>
    password.length >= minimumNewPasswordLength;
