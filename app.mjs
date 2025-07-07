import express from 'express';
import session from 'express-session';
import path from 'path';
import fetch from 'node-fetch';
import { AuthenticationClient } from 'auth0';
import Stripe from 'stripe';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const stripe = Stripe(process.env.STRIPE_SECRET_KEY);

// Define getPlanDetails
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
    req.session.destroy(() => {
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
        res.render('usage', {
            planName: planDetails.planName,
            currentCalls: planDetails.currentCalls,
            apiLimit: planDetails.apiLimit
        });
    } catch (error) {
        res.send('Error fetching plan details');
    }
});

// Profile page
app.get('/profile', async (req, res) => {
    if (!req.session.accessToken) {
        return res.redirect('/login');
    }
    const planDetails = await getPlanDetails(req.session.accessToken);
    const userEmail = 'user@example.com'; // Placeholder email
    res.render('profile', {
        userEmail: userEmail,
        planName: planDetails.planName,
        currentCalls: planDetails.currentCalls,
        apiLimit: planDetails.apiLimit
    });
});

// Settings page
app.get('/settings', async (req, res) => {
    if (!req.session.accessToken) {
        return res.redirect('/login');
    }
    const planDetails = await getPlanDetails(req.session.accessToken);
    const userEmail = 'user@example.com'; // Placeholder email
    res.render('settings', {
        userEmail: userEmail,
        planName: planDetails.planName
    });
});

// Store page
app.get('/store', (req, res) => {
    const plans = [
        { name: "Basic Plan", price: 1200, apiPrice: 50, consultingRate: 200 },   // price in cents/year
        { name: "Premium Plan", price: 6000, apiPrice: 200, consultingRate: 400 }
    ];
    res.render('store', { stripePublishableKey: process.env.STRIPE_PUBLISHABLE_KEY, plans: plans });
});

// Stripe checkout
app.post('/checkout', async (req, res) => {
    const { plan } = req.body;
    try {
        // Adjust price based on the monthly API price in cents
        let amount = 1000; // fallback default price

        if (plan === 'basicplan') {
            amount = 5000; // $50/month => 5000 cents
        } else if (plan === 'premiumplan') {
            amount = 20000; // $200/month => 20000 cents
        } else if (plan === 'premiumbundle') {
            amount = 200000; // Example: $2,000/month => 200000 cents
        } else if (plan === 'riskcompliancebundle') {
            amount = 250000; // Example: $2,500/month => 250000 cents
        }

        const session = await stripe.checkout.sessions.create({
            payment_method_types: ['card'],
            line_items: [
                {
                    price_data: {
                        currency: 'usd',
                        product_data: {
                            name: plan,
                        },
                        unit_amount: amount,
                    },
                    quantity: 1,
                },
            ],
            mode: 'payment',
            success_url: `${process.env.BASE_URL}/checkout-success?session_id={CHECKOUT_SESSION_ID}`,
            cancel_url: `${process.env.BASE_URL}/store`,
        });

        res.json({ sessionId: session.id });
    } catch (err) {
        console.error('Error creating checkout session:', err);
        res.status(500).send('Error creating checkout session');
    }
});

// Checkout success page
app.get('/checkout-success', (req, res) => {
    res.render('checkout');
});

// 404 handler
app.use((req, res) => {
    res.status(404).render('error');
});

// Start server
const port = process.env.PORT || 8080;
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
