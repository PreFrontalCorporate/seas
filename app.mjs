import express from 'express';
import session from 'express-session';
import path from 'path';
import fetch from 'node-fetch';
import { AuthenticationClient } from 'auth0';
import Stripe from 'stripe';
import dotenv from 'dotenv';
import crypto from 'crypto';
import Redis from 'ioredis';

dotenv.config();

const app = express();
const stripe = Stripe(process.env.STRIPE_SECRET_KEY);
const redis = new Redis(process.env.REDIS_URL || "redis://localhost:6379");

const getPlanDetails = async (accessToken) => {
    return {
        planName: 'Basic Plan',
        currentCalls: 50,
        apiLimit: 100
    };
};

const auth0Client = new AuthenticationClient({
    domain: process.env.AUTH0_DOMAIN,
    clientId: process.env.AUTH0_CLIENT_ID,
    clientSecret: process.env.AUTH0_CLIENT_SECRET,
    redirectUri: `${process.env.BASE_URL}/callback`,
});

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

app.get('/', (req, res) => {
    res.render('landing', {
        imagePath: '/images/seas_logo.png',
        title: "Welcome to SEAS",
        subtitle: "Your gateway to seamless API and cloud management",
        buttonText: "Login",
        loginUrl: "/login"
    });
});

app.get('/login', (req, res) => {
    const authUrl = `https://${process.env.AUTH0_DOMAIN}/authorize?client_id=${process.env.AUTH0_CLIENT_ID}&response_type=code&redirect_uri=${process.env.BASE_URL}/callback`;
    res.redirect(authUrl);
});

app.get('/callback', async (req, res) => {
    console.log('Auth0 Callback Route Hit');
    const { code } = req.query;

    if (!code) {
        return res.send("No authorization code received");
    }

    try {
        const tokenResponse = await fetch(`https://${process.env.AUTH0_DOMAIN}/oauth/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
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
        req.session.clientId = tokenData.access_token.slice(0, 12); // Simplified fake client ID
        res.redirect('/usage');
    } catch (err) {
        console.log('Error during Auth0 callback:', err);
        res.send('Error during Auth0 callback');
    }
});

app.get('/logout', (req, res) => {
    req.session.destroy(() => {
        res.redirect(`https://${process.env.AUTH0_DOMAIN}/v2/logout?returnTo=${process.env.BASE_URL}`);
    });
});

app.get('/usage', async (req, res) => {
    console.log('Accessing /usage route');
    if (!req.session.accessToken || !req.session.clientId) {
        console.log('No access token or client ID found, redirecting to login');
        return res.redirect('/login');
    }

    try {
        const planDetails = await getPlanDetails(req.session.accessToken);
        let apiSecret = await redis.get(`user:${req.session.clientId}:api_secret`);
        if (!apiSecret) {
            apiSecret = crypto.randomBytes(24).toString('base64url');
            await redis.set(`user:${req.session.clientId}:api_secret`, apiSecret);
        }

        res.render('usage', {
            usage: planDetails,
            api_secret: apiSecret
        });
    } catch (error) {
        console.error('Error fetching plan details or API secret:', error);
        res.send('Error fetching usage information');
    }
});

app.post('/api/regenerate_secret', async (req, res) => {
    if (!req.session.clientId) {
        return res.redirect('/login');
    }

    const newSecret = crypto.randomBytes(24).toString('base64url');
    await redis.set(`user:${req.session.clientId}:api_secret`, newSecret);

    res.redirect('/usage');
});

// ✅ External API secret validation route
app.post('/api/validate_secret_external', async (req, res) => {
    const { api_secret, client_id } = req.body;
    if (!client_id || !api_secret) {
        return res.status(400).json({ message: "Missing client_id or api_secret" });
    }

    const storedSecret = await redis.get(`user:${client_id}:api_secret`);
    if (!storedSecret) {
        return res.status(404).json({ message: "No secret found for this client_id" });
    }

    if (storedSecret === api_secret) {
        return res.json({ message: "Secret is valid!" });
    } else {
        return res.status(401).json({ message: "Invalid secret!" });
    }
});

// ✅ Permanent key-based endpoint (callable from anywhere using Authorization header)
app.post('/api/some_endpoint', async (req, res) => {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ message: "Missing or invalid Authorization header" });
    }

    const apiSecret = authHeader.split(' ')[1];

    const keys = await redis.keys('user:*:api_secret');
    let clientId = null;
    for (const key of keys) {
        const stored = await redis.get(key);
        if (stored === apiSecret) {
            clientId = key.split(':')[1];
            break;
        }
    }

    if (!clientId) {
        return res.status(401).json({ message: "Invalid API secret" });
    }

    // ✅ You now have clientId — can add rate limits, usage checks, etc.
    res.json({ message: `API call successful for client ${clientId}` });
});

app.get('/profile', async (req, res) => {
    if (!req.session.accessToken) return res.redirect('/login');
    const planDetails = await getPlanDetails(req.session.accessToken);
    res.render('profile', {
        userEmail: 'user@example.com',
        planName: planDetails.planName,
        currentCalls: planDetails.currentCalls,
        apiLimit: planDetails.apiLimit
    });
});

app.get('/settings', async (req, res) => {
    if (!req.session.accessToken) return res.redirect('/login');
    const planDetails = await getPlanDetails(req.session.accessToken);
    res.render('settings', {
        userEmail: 'user@example.com',
        planName: planDetails.planName
    });
});

app.get('/store', (req, res) => {
    const plans = [
        { name: "Basic Plan", price: 1200, apiPrice: 50, consultingRate: 200 },
        { name: "Premium Plan", price: 6000, apiPrice: 200, consultingRate: 400 }
    ];
    res.render('store', { stripePublishableKey: process.env.STRIPE_PUBLISHABLE_KEY, plans: plans });
});

app.post('/checkout', async (req, res) => {
    const { plan } = req.body;
    try {
        let amount = 1000;
        if (plan === 'basicplan') amount = 5000;
        else if (plan === 'premiumplan') amount = 20000;
        else if (plan === 'premiumbundle') amount = 200000;
        else if (plan === 'riskcompliancebundle') amount = 250000;

        const session = await stripe.checkout.sessions.create({
            payment_method_types: ['card'],
            line_items: [
                {
                    price_data: {
                        currency: 'usd',
                        product_data: { name: plan },
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

app.get('/checkout-success', (req, res) => {
    res.render('checkout');
});

app.use((req, res) => {
    res.status(404).render('error');
});

// ✅ Listen on 0.0.0.0 for external access
const port = process.env.PORT || 8080;
app.listen(port, "0.0.0.0", () => {
    console.log(`Server is running on http://0.0.0.0:${port}`);
});
