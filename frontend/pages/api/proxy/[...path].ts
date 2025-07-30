// import http from "http";
// import https from "https";
// import type { NextApiRequest, NextApiResponse } from "next";
// import { URL } from "url";

// export const config = {
//   api: {
//     bodyParser: false,
//   },
// };

// function handler(req: NextApiRequest, res: NextApiResponse) {
//   return new Promise<void>((resolve) => {
//     if (!["GET", "POST", "PUT", "DELETE"].includes(req.method || "")) {
//       console.log("Method not allowed");
//       res.status(405).json({ message: "Method not allowed" });
//       resolve();
//     }

//     const targetUrl = new URL(
//       req.url?.replace(/^\/api\/proxy/, "") || "",
//       process.env.BACKEND_HOST,
//     );

//     const options = {
//       method: req.method,
//       headers: req.headers,
//       timeout: 30000, // 30 seconds timeout
//     };

//     // Choose http or https module based on the protocol
//     const requester = targetUrl.protocol === "https:" ? https : http;

//     const proxyReq = requester.request(targetUrl, options, (proxyRes) => {
//       res.writeHead(proxyRes.statusCode || 200, proxyRes.headers);
//       proxyRes.pipe(res);
//     });

//     req.pipe(proxyReq);

//     proxyReq.on("error", (error) => {
//       res
//         .status(500)
//         .json({ message: "Proxy request error", error: error.message });
//       resolve();
//     });

//     res.on("finish", () => {
//       resolve();
//     });

//     req.on("error", (error) => {
//       console.error("Request error:", error);
//       res.status(500).json({ message: "Request error", error: error.message });
//       resolve();
//     });

//     res.on("error", (error) => {
//       console.error("Response error:", error);
//       resolve();
//     });
//   });
// }

// export default handler;
