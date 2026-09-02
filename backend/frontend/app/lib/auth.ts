import Cookies from "js-cookie";

const TOKEN_KEY = "medbot_token";
const USER_KEY = "medbot_user";

export interface User {
    id: string;
    email: string;
    full_name: string
}

export function saveAuth(token:string, user:User):void {
    Cookies.set(TOKEN_KEY, token,{expires:1})
    Cookies.set(USER_KEY, JSON.stringify(user),{expires:1})
}

export function getToken():string | undefined {
    return Cookies.get(TOKEN_KEY)
}

export function getUser(): User | null {
    const raw = Cookies.get(USER_KEY);
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch {
        return null;
    }
}

export function isLoggedIn():boolean {
    return !!getToken()
}

export function logout(): void {
    Cookies.remove(TOKEN_KEY, { path: "/" });
    Cookies.remove(USER_KEY, { path: "/" });
}