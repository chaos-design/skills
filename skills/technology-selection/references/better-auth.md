
### BetterAuth

**Reference**
- Documentation: https://www.better-auth.com/

**Implementation Guide**

1. **Install Dependencies**
   ```bash
   npm install better-auth
   ```

2. **Backend Configuration**
   Create `utils/auth.ts`:
   ```ts
   import { betterAuth } from "better-auth";
   // Import your DB adapter (e.g., drizzleAdapter, mongodbAdapter)
   
   export const auth = betterAuth({
       // database: drizzleAdapter(db, { provider: "pg" }), 
       emailAndPassword: {
           enabled: true,
       },
   });
   ```

3. **API Handler**
   Mount handler at `/api/auth/*`:
   ```ts
   import { toNodeHandler } from "better-auth/node";
   import { auth } from "./utils/auth";
   
   // In your API route handler
   export const handler = toNodeHandler(auth);
   ```

4. **Frontend Client**
   Create `lib/auth-client.ts`:
   ```ts
   import { createAuthClient } from "better-auth/react";
   
   export const authClient = createAuthClient({
       baseURL: "http://localhost:3000/api/auth" // Adjust to your backend URL
   });
   ```

5. **Usage (React Component)**
   ```tsx
   import { authClient } from "@/lib/auth-client";
   
   function Login() {
       const signIn = async () => {
           await authClient.signIn.email({
               email: "user@example.com",
               password: "password",
               callbackURL: "/dashboard"
           });
       };
       
       return <button onClick={signIn}>Sign In</button>;
   }
   ```
