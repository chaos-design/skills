
### Supabase

**Reference**
- Documentation: https://supabase.com/docs/guides/database/overview

**Implementation Guide**

1. **Install Dependencies**
   ```bash
   npm install @supabase/supabase-js
   ```

2. **Configuration**
   Create `lib/supabase.ts`:
   ```ts
   import { createClient } from '@supabase/supabase-js'

   const supabaseUrl = process.env.VITE_SUPABASE_URL!
   const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY!

   export const supabase = createClient(supabaseUrl, supabaseKey)
   ```

3. **Env Setup**
   Add to `.env`:
   ```env
   VITE_SUPABASE_URL=your-project-url
   VITE_SUPABASE_ANON_KEY=your-anon-key
   ```

4. **Usage Example (Data Fetching)**
   ```tsx
   import { useEffect, useState } from 'react'
   import { supabase } from '@/lib/supabase'

   function TodoList() {
     const [todos, setTodos] = useState([])

     useEffect(() => {
       getTodos()
     }, [])

     async function getTodos() {
       const { data } = await supabase.from('todos').select()
       if (data) setTodos(data)
     }

     return (
       <ul>
         {todos.map(todo => (
           <li key={todo.id}>{todo.title}</li>
         ))}
       </ul>
     )
   }
   ```
