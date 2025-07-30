import React from "react";

import MainParentComponent from "@/components/main-component";

export default function Home() {
  console.log("HELLO MATE INSIDE PAGE");
  console.log("process.env INSIDE PAGE", process.env.NEXT_PUBLIC_API_URL);
  console.log("API_BASE_URL INSIDE PAGE", process.env.NEXT_PUBLIC_API_URL);

  return (
    <div className="">
      <MainParentComponent />
    </div>
  );
}
