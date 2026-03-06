import { promises as fs } from "fs";
import path from "path";

export type Fact = {
  text: string;
  source_url: string;
};

export type Source = {
  name: string;
  url: string;
};

export type StakeholderQuote = {
  speaker: string;
  quote: string;
  url: string;
};

export type Story = {
  slug: string;
  headline: string;
  context?: string;
  category?: string;
  facts: Fact[];
  sources: Source[];
  stakeholder_quotes?: StakeholderQuote[];
};

export type OngoingTopic = {
  slug: string;
  topic: string;
  summary: string;
  timeline: Array<{ date: string; text: string; source_url: string }>;
  primary_sources?: Source[];
};

export type GoodDevelopment = {
  headline: string;
  facts: Fact[];
};

export type DailyData = {
  date: string;
  top_stories: Story[];
  ongoing_topics: OngoingTopic[];
  good_developments: GoodDevelopment[];
  optional_reflection?: string;
};

export type TopicsData = {
  topics: OngoingTopic[];
};

export async function loadDaily(): Promise<DailyData> {
  const filePath = path.join(process.cwd(), "data", "daily.json");
  const raw = await fs.readFile(filePath, "utf8");
  return JSON.parse(raw);
}

export async function loadTopics(): Promise<TopicsData> {
  const filePath = path.join(process.cwd(), "data", "topics.json");
  const raw = await fs.readFile(filePath, "utf8");
  return JSON.parse(raw);
}
