import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export default function Login() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [email, setEmail] = useState("");
  const [step, setStep] = useState("email"); // email, password, register
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [error, setError] = useState("");

  const checkEmail = async () => {
    if (!email) return;
    const res = await fetch(
      `http://localhost:8000/v1/users/${encodeURIComponent(email)}/exists`
    );
    const data = await res.json();
    setStep(data.exists ? "password" : "register");
  };

  const handleLogin = async () => {
    const res = await fetch("http://localhost:8000/v1/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: email, password }),
    });
    if (res.ok) {
      const data = await res.json();
      // persist the raw token for useApi to pick up:
      localStorage.setItem("auth", JSON.stringify({ token: data.token }));
      setUser({
        token: data.token,
        email,
        first_name: data.first_name,
        last_name: data.last_name,
      });
      navigate("/");
    } else {
      setError("Invalid credentials");
    }
  };

  const handleRegister = async () => {
    if (password !== password2) {
      setError("Passwords do not match");
      return;
    }
    const res = await fetch("http://localhost:8000/v1/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: email,
        password,
        first_name: firstName,
        last_name: lastName,
      }),
    });
    if (res.ok) {
      const data = await res.json();
      // persist the raw token for useApi to pick up:
      localStorage.setItem("auth", JSON.stringify({ token: data.token }));
      setUser({
        token: data.token,
        email,
        first_name: data.first_name,
        last_name: data.last_name,
      });
      navigate("/");
    } else {
      const info = await res.json().catch(() => ({}));
      setError(info.detail || "Registration failed");
    }
  };

  return (
    <div className="flex items-center justify-center py-8">
      <div className="w-full max-w-sm space-y-4">
        {step === "email" && (
          <>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="border p-2 w-full rounded"
              placeholder="Email"
            />
            <button
              onClick={checkEmail}
              className="w-full bg-indigo-600 text-white p-2 rounded"
            >
              Continue
            </button>
          </>
        )}

        {step === "password" && (
          <>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="border p-2 w-full rounded"
              placeholder="Password"
            />
            <button
              onClick={handleLogin}
              className="w-full bg-indigo-600 text-white p-2 rounded"
            >
              Login
            </button>
          </>
        )}

        {step === "register" && (
          <>
            <input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className="border p-2 w-full rounded"
              placeholder="First name"
            />
            <input
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              className="border p-2 w-full rounded"
              placeholder="Last name"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="border p-2 w-full rounded"
              placeholder="Password"
            />
            <input
              type="password"
              value={password2}
              onChange={(e) => setPassword2(e.target.value)}
              className="border p-2 w-full rounded"
              placeholder="Repeat password"
            />
            <button
              onClick={handleRegister}
              className="w-full bg-indigo-600 text-white p-2 rounded"
            >
              Register
            </button>
          </>
        )}

        {error && <p className="text-red-600 text-sm">{error}</p>}
      </div>
    </div>
  );
}
