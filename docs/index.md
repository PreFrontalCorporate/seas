# 📄 Welcome to CBB Homes API Documentation

Welcome to the official documentation for the CBB Homes API suite. Here, you'll learn how to authenticate, integrate, and use each of our robust analytics and financial optimization programs securely using your unique API key.

---

## 🎯 Overview

The CBB Homes suite offers a range of advanced modules for risk management, portfolio optimization, and financial analytics, including:

* **CVaR App** (Conditional Value at Risk)
* **Wasserstein App** (Robust Portfolio Optimizer)
* **Heavy-Tail Volatility Simulator**
* **Kolmogorov Complexity Explorer**

All modules require API authentication using your API secret key.

---

## 🔑 API Authentication

### How to get your API key

1. **Login** via Auth0 on [cbb.homes](https://cbb.homes) and navigate to your usage dashboard.
2. If you do not have a key yet, click **Generate API Secret**.
3. You can **regenerate** your API key at any time. This will immediately invalidate the old one.

### Using your API key

Every API call must include the following HTTP header:

```http
Authorization: Bearer YOUR_API_SECRET
```

**Example (cURL):**

```bash
curl -H "Authorization: Bearer YOUR_API_SECRET" https://cbb.homes/cvar/some_endpoint
```

---

## 💼 CVaR App

**URL prefix**: `/cvar`

* Designed for risk estimation under extreme market conditions.
* Uses robust convex optimization and supports scenarios such as tail loss estimation.

**How to call:**

```bash
curl -X POST https://cbb.homes/cvar/estimate \
     -H "Authorization: Bearer YOUR_API_SECRET" \
     -d '{"portfolio": [0.3, 0.7], "confidence_level": 0.95}'
```

---

## 🌊 Wasserstein Robust Portfolio Optimizer

**URL prefix**: `/wasserstein`

* Optimizes portfolios under distributional uncertainty using Wasserstein distances.
* Ideal for robust asset allocation.

**How to call:**

```bash
curl -X POST https://cbb.homes/wasserstein/optimize \
     -H "Authorization: Bearer YOUR_API_SECRET" \
     -d '{"assets": [...], "risk_aversion": 0.5}'
```

---

## 🌀 Heavy-Tail Volatility Simulator

**URL prefix**: `/heavy-tail`

* Models heavy-tail risks to simulate volatility shocks.
* Useful for stress testing and extreme risk modeling.

**How to call:**

```bash
curl -X POST https://cbb.homes/heavy-tail/simulate \
     -H "Authorization: Bearer YOUR_API_SECRET" \
     -d '{"shock_magnitude": 3.0, "periods": 100}'
```

---

## 🧩 Kolmogorov Complexity Explorer

**URL prefix**: `/kolmogorov`

* Explores complexity-based portfolio construction.
* Useful for non-parametric and information-theoretic approaches.

**How to call:**

```bash
curl -X POST https://cbb.homes/kolmogorov/explore \
     -H "Authorization: Bearer YOUR_API_SECRET" \
     -d '{"data": [...]}'
```

---

## ⚙️ Example Flow

1️⃣ Login →
2️⃣ Go to **Usage** →
3️⃣ Copy your **API secret** →
4️⃣ Include it as a Bearer token in your requests →
5️⃣ Call any of the endpoints above.

---

## 💬 Support

For help or questions, please reach out to [prefrontalcorporate@gmail.com](mailto:prefrontalcorporate@gmail.com).

---

### 📝 Additional Security Notes

* Store your API secret securely — treat it like a password.
* Regenerate your key if you suspect it has been exposed.
* Each API secret is tied to your client ID and usage limits.

---

✅ Ready to integrate? Start exploring on [cbb.homes](https://cbb.homes)!
