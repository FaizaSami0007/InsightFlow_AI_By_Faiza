"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Lock, Mail, Sparkles } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/stores/use-auth-store";

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, error, clearError, isAuthenticated } = useAuthStore();

  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);
  const [clientErrors, setClientErrors] = React.useState<{ email?: string; password?: string }>({});

  React.useEffect(() => {
    if (isAuthenticated) {
      router.push("/datasets");
    }
  }, [isAuthenticated, router]);

  const validate = (): boolean => {
    const errs: { email?: string; password?: string } = {};
    if (!email.trim()) {
      errs.email = "Email address is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errs.email = "Please enter a valid email address.";
    }

    if (!password) {
      errs.password = "Password is required.";
    }

    setClientErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!validate()) return;

    const success = await login(email, password);
    if (success) {
      router.push("/datasets");
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-cloud px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center">
          <Link
            href="/"
            className="flex h-12 w-12 items-center justify-center rounded-2xl bg-teal text-white shadow-soft transition-transform hover:scale-105 focus-visible:ring-2 focus-visible:ring-teal"
            aria-label="Back to InsightFlow AI Home"
          >
            <Sparkles className="h-6 w-6" />
          </Link>
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-ink">Welcome back</h1>
          <p className="mt-1 text-xs text-slate">
            Sign in to access your datasets and grounded analytical workspace
          </p>
        </div>

        {/* Login Card */}
        <Card className="shadow-soft-md border-border bg-surface">
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>Enter your credentials below</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit} noValidate>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="danger">
                  <AlertTitle>Authentication Failed</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Input
                label="Email Address"
                type="email"
                id="login-email"
                autoComplete="email"
                placeholder="analyst@company.com"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (clientErrors.email) setClientErrors((prev) => ({ ...prev, email: undefined }));
                }}
                error={clientErrors.email}
                leftIcon={<Mail className="h-4 w-4" />}
                required
              />

              <div className="relative">
                <Input
                  label="Password"
                  type={showPassword ? "text" : "password"}
                  id="login-password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (clientErrors.password) setClientErrors((prev) => ({ ...prev, password: undefined }));
                  }}
                  error={clientErrors.password}
                  leftIcon={<Lock className="h-4 w-4" />}
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-slate hover:text-ink focus-visible:outline-none"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  }
                  required
                />
              </div>
            </CardContent>
            <CardFooter className="flex flex-col space-y-4 pt-2">
              <Button
                type="submit"
                variant="primary"
                className="w-full"
                isLoading={isLoading}
              >
                Sign In
              </Button>

              <div className="text-center text-xs text-slate">
                Don&apos;t have an account?{" "}
                <Link
                  href="/register"
                  className="font-semibold text-teal hover:underline focus-visible:ring-2 focus-visible:ring-teal"
                >
                  Create an account
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
