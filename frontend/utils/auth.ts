// import { jwtVerify, JWTPayload, decodeJwt, errors, importSPKI } from "jose";
// import { DecodedKeycloakToken, ParsedAuthTokenResult } from '@/utils/types/auth'
// import { headers } from "next/headers";

// export async function isAuthorisedUser(header: string): Promise<boolean> {
//   if (!process.env.REPO) {
//     console.error("REPO environment variable not set");
//     return false;
//   }

//   const parsedToken = await parseAuthToken(header)

//   if (!parsedToken) {
//     console.error("No token found for user");
//     return false;
//   }

//   return parsedToken.roles.some(role =>
//     role === process.env.REPO || role === "local-testing"
//   )
// }

// async function parseAuthToken(header: string): Promise<ParsedAuthTokenResult | null> {
//   if (!header) {
//     console.error("No auth token provided to parse")
//     return null;
//   }

//   let verifyJwtSource = !process.env.DISABLE_AUTH_SIGNATURE_VERIFICATION;
//   let tokenContent = await getDecodedJwt(header, verifyJwtSource);

//   if (!tokenContent) {
//     return null;
//   }

//   let email = tokenContent.email;
//   if (!email) {
//     console.error("No email found in token");
//     return null;
//   }

//   let realmAccess = tokenContent.realm_access;
//   if (!realmAccess) {
//     console.error("No realm access information found in token");
//     return null;
//   }

//   let roles = tokenContent.realm_access.roles || [];
//   console.debug(`Roles found for user ${email}: ${roles}`);
//   return {
//     email,
//     roles,
//   }
// }

// async function getDecodedJwt(header: string, verifyJwtSource: boolean): Promise<DecodedKeycloakToken | null> {
//   let decodedToken: JWTPayload | null = null;

//   try {
//     if (verifyJwtSource) {
//       const publicKeyEncoded = process.env.AUTH_PROVIDER_PUBLIC_KEY!;  // This is passed into the environment by ECS
//       const pemPublicKey = convertToPemPublicKey(publicKeyEncoded);
//       const publicKey = await importSPKI(pemPublicKey, "RS256");

//       try {
//         // Verify with signature
//         const { payload } = await jwtVerify(header, publicKey, {
//           algorithms: ["RS256"],
//           audience: "account",
//         });

//         decodedToken = payload;
//       } catch (error) {
//         if (error instanceof errors.JWTExpired) {
//           console.error("JWT has expired:", error.message);
//           return null;
//         } else if (error instanceof errors.JWTInvalid) {
//           console.error("Malformed JWT:", error.message);
//           return null;
//         }
//         console.error("Unexpected JWT verification error:", error);
//         return null;
//       }
//     } else {
//       // Decode without verification
//       try {
//         decodedToken = decodeJwt(header);
//       } catch (error) {
//         console.error("Malformed JWT during decoding:", error);
//         return null;
//       }
//     }
//     return decodedToken as DecodedKeycloakToken;
//   } catch (error) {
//     if (isDomException(error)) {
//       console.error("Unexpected DOMException in getDecodedJwt:", {
//         name: error.name,
//         message: error.message,
//         stack: error.stack,
//       });
//     } else {
//       console.error("Unexpected error in getDecodedJwt:", error);
//     }

//     return null;
//   }
// }

// function isDomException(error: unknown): error is DOMException {
//   return typeof error === "object" &&
//     error !== null &&
//     error.constructor?.name === "DOMException"
// }

// function convertToPemPublicKey(keyBase64: string): string {
//   return `-----BEGIN PUBLIC KEY-----\n${keyBase64}\n-----END PUBLIC KEY-----`;
// }

// export async function getServerSideDecodedToken(): Promise<DecodedKeycloakToken | null> {
//   if (process.env.ENVIRONMENT === "local" || process.env.ENVIRONMENT === "test") {
//     return null;
//   }

//   const sessionHeaders = await headers();
//   const token = sessionHeaders.get("x-amzn-oidc-accesstoken");

//   if (!token) {
//     return null;
//   }

//   const tokenContent = getDecodedJwt(token, true);
//   return tokenContent || null;
// }
