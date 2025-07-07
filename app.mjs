import express from 'express';
import session from 'express-session';
import path from 'path';
import fetch from 'node-fetch';  // Using ES Module import
import { AuthenticationClient } from 'auth0';
import Stripe from 'stripe';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const stripe = Stripe(process.env.STRIPE_SECRET_KEY);

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
    redirectUri: `${process.env.BASE_URL}/callback`,
});

// Use import.meta.url to resolve __dirname
const __dirname = path.dirname(new URL(import.meta.url).pathname);

app.set('view engine', 'ejs');
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.use(session({
    secret: process.env.SESSION_SECRET || 'default_secret_key',
    resave: false,
    saveUninitialized: true,
    cookie: {
        secure: process.env.NODE_ENV === 'production'
    }
}));

// Landing page
app.get('/', (req, res) => {
    res.render('landing', {
        imagePath: '/images/seas_logo.png',
        title: "Welcome to SEAS",
        subtitle: "Your gateway to seamless API and cloud management",
        buttonText: "Login",
        loginUrl: "/login"
    });
});

// Login route
app.get('/login', (req, res) => {
    const authUrl = `https://${process.env.AUTH0_DOMAIN}/authorize?client_id=${process.env.AUTH0_CLIENT_ID}&response_type=code&redirect_uri=${process.env.BASE_URL}/callback`;
    res.redirect(authUrl);
});

// Callback route
app.get('/callback', async (req, res) => {
    console.log('Auth0 Callback Route Hit');
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
        res.redirect('/usage');
    } catch (err) {
        console.log('Error during Auth0 callback:', err);
        res.send('Error during Auth0 callback');
    }
});

// Logout route
app.get('/logout', (req, res) => {
    req.session.destroy((err) => {
        res.redirect(`https://${process.env.AUTH0_DOMAIN}/v2/logout?returnTo=${process.env.BASE_URL}`);
    });
});

// Usage page
app.get('/usage', async (req, res) => {
    console.log('Accessing /usage route');
    if (!req.session.accessToken) {
        console.log('No access token found, redirecting to login');
        return res.redirect('/login');
    }

    try {
        const planDetails = await getPlanDetails(req.session.accessToken);
        console.log('Plan Details:', planDetails);
        res.render('usage', {
            planName: planDetails.planName,
            currentCalls: planDetails.currentCalls,
            apiLimit: planDetails.apiLimit
        });
    } catch (error) {
        console.error('Error fetching plan details:', error);
        res.send('Error fetching plan details');
    }
});

// Profile page
app.get('/profile', (req, res) => {
    res.render('profile');
});

// Settings page
app.get('/settings', (req, res) => {
    res.render('settings');
});

// Store page
app.get('/store', (req, res) => {
    // You can add your plans array here if needed
    res.render('store', { stripePublishableKey: process.env.STRIPE_PUBLISHABLE_KEY, plans: [] });
});

// Stripe checkout
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
                        unit_amount: 1000, // adjust for your product price
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
        console.error('Error creating checkout session:', err);
        res.status(500).send('Error creating checkout session');
    }
});

// 404 handler
app.use((req, res, next) => {
    console.log(`Request to ${req.url} not found`);
    res.status(404).render('error');
});

// Start the server
const port = process.env.PORT || 8080;
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
