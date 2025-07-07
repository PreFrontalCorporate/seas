import express from 'express';
import session from 'express-session';
import path from 'path';
import fetch from 'node-fetch';  // Using ES Module import
import { AuthenticationClient } from 'auth0';  // Corrected import for Auth0
import Stripe from 'stripe';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const stripe = Stripe(process.env.STRIPE_SECRET_KEY);  // Your Stripe secret key

// Define the getPlanDetails function
const getPlanDetails = async (accessToken) => {
    return new Promise((resolve) => {
        resolve({
            planName: 'Basic Plan',
            currentCalls: 50,
            apiLimit: 100
        });
    });
};

// Initialize Auth0Client
const auth0Client = new AuthenticationClient({
    domain: process.env.AUTH0_DOMAIN,
    clientId: process.env.AUTH0_CLIENT_ID,
    clientSecret: process.env.AUTH0_CLIENT_SECRET,
    redirectUri: `${process.env.BASE_URL}/callback`,  // Auth0 callback
});

// Use import.meta.url to resolve __dirname in ES Modules
const __dirname = path.dirname(new URL(import.meta.url).pathname);

// Set up the view engine and static file path
app.set('view engine', 'ejs');
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Session middleware for maintaining login state
app.use(session({
    secret: process.env.SESSION_SECRET || 'default_secret_key',  // Store the secret in .env
    resave: false,
    saveUninitialized: true,
    cookie: {
        secure: process.env.NODE_ENV === 'production' // Secure cookies in production
    }
}));

// Routes

// Landing page - Home route with a big Login button
app.get('/', (req, res) => {
    res.render('landing', {
        imagePath: '/images/seas_logo.png',  // Path to the image you uploaded
        title: "Welcome to SEAS",
        subtitle: "Your gateway to seamless API and cloud management",
        buttonText: "Login",
        loginUrl: "/login"
    });
});

// Login route - redirect to Auth0
app.get('/login', (req, res) => {
    const authUrl = `https://${process.env.AUTH0_DOMAIN}/authorize?client_id=${process.env.AUTH0_CLIENT_ID}&response_type=code&redirect_uri=${process.env.BASE_URL}/callback`;
    res.redirect(authUrl);
});

// Auth0 Callback route - handle Auth0 callback after login
app.get('/callback', async (req, res) => {
    const { code } = req.query;

    if (!code) {
        return res.send("No authorization code received");
    }

    try {
        const tokenResponse = await fetch(`https://${process.env.AUTH0_DOMAIN}/oauth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                client_id: process.env.AUTH0_CLIENT_ID,
                client_secret: process.env.AUTH0_CLIENT_SECRET,
                code,
                redirect_uri: `${process.env.BASE_URL}/callback`,
                grant_type: 'authorization_code'
            }),
        });

        const tokenData = await tokenResponse.json();
        req.session.accessToken = tokenData.access_token;
        res.redirect('/usage');  // Redirect to usage page after login
    } catch (err) {
        res.send('Error during Auth0 callback');
    }
});

// Logout route - Clear session and redirect to Auth0 logout
app.get('/logout', (req, res) => {
    req.session.destroy((err) => {
        // Redirect to Auth0 logout page with a return URL to your homepage
        res.redirect(`https://${process.env.AUTH0_DOMAIN}/v2/logout?returnTo=${process.env.BASE_URL}`);
    });
});

// Usage page - Display the user's API usage after login
app.get('/usage', async (req, res) => {
    if (!req.session.accessToken) {
        return res.redirect('/login');  // Ensure the user is logged in
    }

    try {
        const planDetails = await getPlanDetails(req.session.accessToken);  // Fetch user plan details using the access token
        res.render('usage', {
            planName: planDetails.planName,
            currentCalls: planDetails.currentCalls,
            apiLimit: planDetails.apiLimit
        });
    } catch (error) {
        res.send('Error fetching plan details');
    }
});

// Stripe Checkout session creation route
app.post('/checkout', async (req, res) => {
    const { plan } = req.body;
    try {
        const session = await stripe.checkout.sessions.create({
            payment_method_types: ['card'],
            line_items: [
                {
                    price_data: {
                        currency: 'usd',
                        product_data: {
                            name: plan,
                        },
                        unit_amount: 1000,  // Adjust for your product's price
                    },
                    quantity: 1,
                },
            ],
            mode: 'payment',
            success_url: `${process.env.BASE_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
            cancel_url: `${process.env.BASE_URL}/cancel`,
        });

        res.json({ sessionId: session.id });
    } catch (err) {
        res.status(500).send('Error creating checkout session');
    }
});

// Error handling page for 404
app.use((req, res, next) => {
    res.status(404).render('error');
});

// Start the server
const port = process.env.PORT || 8080;
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});

