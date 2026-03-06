import { loadDaily } from "@/lib/data";
import DailyEdition from "./DailyEdition";

export default async function HomePage() {
  const daily = await loadDaily();
  return <DailyEdition daily={daily} />;
}
