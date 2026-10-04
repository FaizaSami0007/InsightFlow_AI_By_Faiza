"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Check, Eye, EyeOff, Lock, Mail, Sparkles, User as UserIcon, X } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/stores/use-auth-store";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading, error, clearError, isAuthenticated } = useAuthStore();

  const [fullName, setFullName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);
  const [clientErrors, setClientErrors] = React.useState<{ fullName?: string; email?: string; password?: string }>({});

  React.useEffect(() => {
    if (isAuthenticated) {
      router.push("/datasets");
    }
  }, [isAuthenticated, router]);

  const hasMinLength = password.length >= 8;
  const hasNumberOrSymbol = /[0-9!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password);

  const validate = (): boolean => {
    const errs: { fullName?: string; email?: string; password?: string } = {};

    if (!fullName.trim()) {
      errs.fullName = "Full name is required.";
    }

    if (!email.trim()) {
      errs.email = "Email address is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errs.email = "Please enter a valid email address.";
    }

    if (!password) {
      errs.password = "Password is required.";
    } else if (!hasMinLength || !hasNumberOrSymbol) {
      errs.password = "Please satisfy all password strength requirements.";
    }

    setClientErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!validate()) return;

    const success = await register(email, password, fullName);
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
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-ink">Create an account</h1>
          <p className="mt-1 text-xs text-slate">
            Get started with AI analytics, data profiling, and verified dashboard generation
          </p>
        </div>

        {/* Register Card */}
        <Card className="shadow-soft-md border-border bg-surface">
          <CardHeader>
            <CardTitle>Register</CardTitle>
            <CardDescription>Fill in your details below to create your account</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit} noValidate>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="danger">
                  <AlertTitle>Registration Failed</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Input
                label="Full Name"
                type="text"
                id="register-fullname"
                autoComplete="name"
                placeholder="Jane Doe"
                value={fullName}
                onChange={(e) => {
                  setFullName(e.target.value);
                  if (clientErrors.fullName) setClientErrors((prev) => ({ ...prev, fullName: undefined }));
                }}
                error={clientErrors.fullName}
                leftIcon={<UserIcon className="h-4 w-4" />}
                required
              />

              <Input
                label="Work Email Address"
                type="email"
                id="register-email"
                autoComplete="email"
                placeholder="jane.doe@company.com"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (clientErrors.email) setClientErrors((prev) => ({ ...prev, email: undefined }));
                }}
                error={clientErrors.email}
                leftIcon={<Mail className="h-4 w-4" />}
                required
              />

              <div className="relative space-y-2">
                <Input
                  label="Password"
                  type={showPassword ? "text" : "password"}
                  id="register-password"
                  autoComplete="new-password"
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

                {/* Password Strength Checklist */}
                {password.length > 0 && (
                  <div className="rounded-lg bg-cloud p-2.5 text-[11px] space-y-1">
                    <div className="flex items-center gap-1.5 font-medium text-slate">
                      {hasMinLength ? (
                        <Check className="h-3.5 w-3.5 text-teal" />
                      ) : (
                        <X className="h-3.5 w-3.5 text-danger" />
                      )}
                      <span className={hasMinLength ? "text-teal" : "text-slate"}>
                        At least 8 characters
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 font-medium text-slate">
                      {hasNumberOrSymbol ? (
                        <Check className="h-3.5 w-3.5 text-teal" />
                      ) : (
                        <X className="h-3.5 w-3.5 text-danger" />
                      )}
                      <span className={hasNumberOrSymbol ? "text-teal" : "text-slate"}>
                        Contains a number or special character
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
            <CardFooter className="flex flex-col space-y-4 pt-2">
              <Button
                type="submit"
                variant="primary"
                className="w-full"
                isLoading={isLoading}
              >
                Create Account
              </Button>

              <div className="text-center text-xs text-slate">
                Already have an account?{" "}
                <Link
                  href="/login"
                  className="font-semibold text-teal hover:underline focus-visible:ring-2 focus-visible:ring-teal"
                >
                  Sign in
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
