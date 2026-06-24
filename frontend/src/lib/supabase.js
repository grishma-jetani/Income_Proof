import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = 'https://YOURPROJECT.supabase.co'   // replace with yours
const SUPABASE_ANON_KEY = 'YOUR_ANON_KEY_HERE'                        // replace with yours

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)