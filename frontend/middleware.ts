import { NextRequest, NextResponse } from 'next/server'
import { isAuthorisedUser } from "@/utils/auth"

// Define paths that should be public (no authorisation required)
const PUBLIC_PATHS = [
  '/unauthorised',
]

const TEST_AUTHORISATION_JWT = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOiIxNzM5ODk2MTk5IiwiaWF0IjoiMTczOTg5NTg5OSIsImF1dGhfdGltZSI6IjE3Mzk4OTM1MjkiLCJqdGkiOiIyYmVmOGI1ZS0yOGY0LTQ2OWQtYWQ2My1lZjJlNDgxNzliODYiLCJpc3MiOiJodHRwczovL2xvY2FsLXRlc3Rpbmcub2JmdXNjYXRlZC50ZXN0LmRvbWFpbi5nb3YudWsvcmVhbG1zL29iZnVzY2F0ZWQiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiYmMzNzNkZTQtNDAyMi00NmIyLTgxNTEtZjA0NjEzNzhlOWNiIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoibWludXRlIiwic2lkIjoiYzM2NmE5ZmUtMDNiNC00MjIxLWI0ZWItOTE0MzMzNWFhNjUyIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL2xvY2FsLXRlc3Rpbmcub2JmdXNjYXRlZC50ZXN0LmRvbWFpbi5nb3YudWsiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbImxvY2FsLXRlc3RpbmciXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOiJ0cnVlIiwicHJlZmVycmVkX3VzZXJuYW1lIjoidGVzdEB0ZXN0LmNvLnVrIiwiZW1haWwiOiJ0ZXN0QHRlc3QuY28udWsifQ.Pmlltl1M0Q9EAkU96J_zkPJUjjh2TGhQGzfi0v2J-IrxUt1KTnGEcnEk09TUJjdCuyIgO9YEH-uGj5MihnGj6PqCQjq17lWP5YUjYyjgrULfgM6jZ_659RK31wZdRg_72yiy-BeVd-c-v7UzRtdTXIMkwn_aWEIp7own__jfZV_E_32KfelgtwzljVGHjGXdz_Irg6_2B4lbRn8ipWAn3SDlM9Cj8aJw7q5qq7XPk9KkXclivi4bMQJ9RNgMxtgitFtdINRF1A9_pkbERM1LliAgvW-FTLwmVECAGDQyoE8xDQuti8JgixvM22WfpdznSLd2gWAWMiyYZJwRxzFSVw"; // pragma: allowlist secret

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Check if the requested path is public
  if (PUBLIC_PATHS.some(path => pathname.startsWith(path))) {
    return NextResponse.next();
  }

  try {
    let token;

    if (process.env.ENVIRONMENT == "local") {
      token = TEST_AUTHORISATION_JWT
    } else {
      token = req.headers.get("x-amzn-oidc-accesstoken");
    }

    if (!token) {
      console.error(`No auth token found in headers when accessing ${pathname}`);
      return redirectToUnauthorised(req);
    }

    if (! await isAuthorisedUser(token)) {
      return redirectToUnauthorised(req);
    }

    return NextResponse.next();
  } catch (error) {
    console.error("Error authorising token:", error)
    return redirectToUnauthorised(req)
  }
}

function redirectToUnauthorised(req: NextRequest) {
  const url = req.nextUrl.clone();
  url.pathname = "/unauthorised";
  return NextResponse.redirect(url);
}

// Configure which paths this middleware should run on
export const config = {
  matcher: [
    // Match all paths except those starting with excluded paths
    // You can customize this as needed
    "/((?!unauthorised|_next/static|_next/image|favicon.ico|api/health).*)",
  ],
};
