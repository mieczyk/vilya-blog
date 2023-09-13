# Overview

This is a simple Flask application with intended CSRF vulnerability. It uses a very simple authentication 
mechanism based on Flask [session](https://flask.palletsprojects.com/en/2.3.x/api/#sessions) object. 
Additionally, it has a very loose [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) policy 
(requests from all sources are allowed). It's been written for demonstration purposes only, so 
**don't use this code in a real-world application**.

The application has the following endpoints:

- `(GET) /` - the home page.
- `(GET|POST) /login` - sign in page. Once the credentials are posted and validated, the *logged_in* flag is stored in the session.
- `(GET) /logout` - sign out. The session is cleared.
- `(GET) /sendout` - example of poorly designed API endpoint. The GET request that triggers potentially dangerous action.
  It actually doesn't do anything, but the warning message is logged when the method is called.
- `(POST) /password` - change password for a signed-in user. The new password should be passed in the request's body in
  JSON format. It's also a dummy method - once called, the proper message is logged.
- `(GET) /exploit` - simulates a CSRF attack.

# Setup

All required dependencies can be installed with [poetry](https://python-poetry.org/):

```bash
poetry install
```

To run the application (it starts the dev server on `http://localhost:5000` address):

```bash
poetry run app.py
```

You can also run some tests with [pytest](https://docs.pytest.org/en/7.4.x/):

```bash
poetry run pytest
```

# CSRF vulnerability

As already mentioned, the application is poorly designed (deliberately) and it's vulnerable to 
[CSRF](https://owasp.org/www-community/attacks/csrf) due to the following reasons:

* Very simple authentication mechanism.
* No anti-CSRF tokens with random values used.
* Very permissive CORS policy (cross-site requests from all origins allowed).
* `GET` request changing the system's state.

## Same-origin exploit

The simplest scenario is when the malicious requests come from the same origin (domain).
For example, if the application is vulnerable to XSS, an attacker may put on a page 
a piece of code that triggers CSRF requests. Take a look at the `templates/exploit.html`:

```html
<img src="http://localhost:5000/sendout"></img>
```

Now, when a signed-in user visits the *infected* page available in the application, a browser will
try to load the image from URL given in the `src` attribute. In our example, it will automatically
trigger the `/sendout` request.

Another example from the `exploit.html` page, but this time triggering the `POST` request:

```html
<img src="#" onerror="fetch('http://localhost:5000/password',{credentials:'include',method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password: 'pwned'})})"></img>
```

The JavaScript code defined in the `onerror` attribute is executed when a browser cannot load an image from given source.
So, the attacker put there the [`fetch()`](https://developer.mozilla.org/en-US/docs/Web/API/fetch) function that
sends the `POST /password` request.

Again, if the user is authenticated (the session cookie is stored in his/her browser), the password will
be changed to the value given in the request:

```
[2023-09-12 20:04:41,828] INFO in app: Password changed to pwned
```

## Cross-origin exploit

Now comes the hard part. Despite the application has a lot of design bugs that should make the CSRF attacks possible,
the modern browsers are on guard duty.

I tried to simulate the CSRF requests from another domain with the following steps (on Linux):

1. Define a custom hostname for the loopback address in `/etc/hosts`. For example
```
127.0.0.1   csrf
```
2. Change the URLs in the `templates/exploit.html` template, from `http://localhost:5000` to `http://csrf:5000` (as defined
   in the `/etc/hosts` file).
3. Set up the CORS policy that allows requests from all domains:
```python
# app.py
# ...
app = Flask(__name__)

CORS(app, supports_credentials=True)
# ...
```
4. Start the Flask application.
5. Visits the `http://csrf:5000` address in a browser and sign in.
6. Go to the `templates` directory and start a simple HTTP server with python 3: `python3 -m http.server 8080`. 
   Now we've got 2 web applications up and running in the system: `http://csrf:5000` (target domain) and 
   `http://localhost:8080` (origin domain).
7. Visit the `http://localhost:8080/exploit.html` URL in the browser. Don't worry about the not parsed 
   [Jinja](https://jinja.palletsprojects.com/en/3.1.x/) template's elements. The `<img>` tags are still parsed.

The results:

- The cross-site attack **worked on the old Firefox browser 91.11.0esr**.
- It **didn't work on Firefox 117.0** because of the [Total Cookie Protection](https://blog.mozilla.org/en/mozilla/firefox-rolls-out-total-cookie-protection-by-default-to-all-users-worldwide/) feature enabled by default. It prevents
  from sending the session cookie to a different domain despite the CORS settings. However, when I manually disabled it,
  the attack succeeded.
- It **didn't work on Chrome 116.0.5845.140**. That's because [Chrome enforces the `SameSite=Lax` flag by default](https://chromestatus.com/feature/5088147346030592) on the cookies. Additionally, if we want to set the flag's value to `None`
  explicitly, the `Secure` flag **must** be set to `true`. So, it won't work for HTTP communication. However, when I generated a self-signed certificate for the Flask application and set up HTTPS communication locally, it worked.
  Of course the `SameSite` flag's value has to be set to `None` for the session cookie in the Flask application.
