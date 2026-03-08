import { promises as fs } from "fs";
import path from "path";

export type Fact = { text: string; source_url: string };
export type Source = { name: string; url: string };
export type StakeholderQuote = { speaker: string; quote: string; url: string; source?: string; perspective?: string; source_outlet?: string };
export type ComponentArticle = { source: string; lean: string; title: string; url: string };
export type KeyParty = { name: string; role: string };

export type Story = {
  slug: string;
  headline: string;
  bottom_line?: string;
  body?: string;
  summary?: string;
  context?: string;
  why_it_matters?: string;
  what_to_watch?: string;
  category?: string;
  key_points?: Fact[];
  facts?: Fact[];
  sources: Source[];
  component_articles?: ComponentArticle[];
  stakeholder_quotes?: StakeholderQuote[];
  is_good_development?: boolean;
  is_negative?: boolean;
  positive_thought?: string;
  related_ongoing?: string;
};

export type OngoingTopic = {
  slug: string;
  topic: string;
  summary: string;
  background?: string;
  started?: string;
  key_facts?: Record<string, string>;
  key_parties?: KeyParty[];
  timeline: Array<{ date: string; text: string; source_url: string }>;
  primary_sources?: Source[];
};

export type GoodDevelopment = {
  slug: string;
  headline: string;
  bottom_line?: string;
  body?: string;
  summary?: string;
  context?: string;
  why_it_matters?: string;
  what_to_watch?: string;
  category?: string;
  key_points?: Fact[];
  facts?: Fact[];
  sources: Source[];
  component_articles?: ComponentArticle[];
  stakeholder_quotes?: StakeholderQuote[];
  is_good_development?: boolean;
  is_negative?: boolean;
  positive_thought?: string;
  related_ongoing?: string;
};

export type NeedToKnow = { headline: string; bottom_line: string };

export type DailyData = {
  date: string;
  need_to_know?: NeedToKnow[];
  top_stories: Story[];
  ongoing_topics: OngoingTopic[];
  good_developments: GoodDevelopment[];
  optional_reflection?: string;
};

export type TopicsData = { topics: OngoingTopic[] };

export async function loadDaily(): Promise<DailyData> {
  const filePath = path.join(process.cwd(), "data", "daily.json");
  return JSON.parse(await fs.readFile(filePath, "utf8"));
}

export async function loadTopics(): Promise<TopicsData> {
  const filePath = path.join(process.cwd(), "data", "topics.json");
  return JSON.parse(await fs.readFile(filePath, "utf8"));
}
