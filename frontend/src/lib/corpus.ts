export type CorpusCompany = { ticker: string; name: string }

export const CORPUS_COMPANIES: CorpusCompany[] = [
  { ticker: 'AAPL', name: 'Apple' },
  { ticker: 'AMZN', name: 'Amazon' },
  { ticker: 'GOOGL', name: 'Alphabet' },
  { ticker: 'MSFT', name: 'Microsoft' },
  { ticker: 'NVDA', name: 'NVIDIA' },
]

export const CORPUS_FISCAL_RANGE = 'FY2021–FY2025'
export const CORPUS_FILING_TYPE = '10-K'

export type StarterPrompt = { category: string; prompt: string }

/** Analyst workflows, drawn from the client brief's example questions. */
export const STARTER_PROMPTS: StarterPrompt[] = [
  {
    category: 'Revenue mix',
    prompt:
      "How did Apple's revenue mix across iPhone, Services, Mac, iPad, and Wearables change from 2021 to 2025, and which category drove the shift?",
  },
  {
    category: 'Segment profitability',
    prompt:
      'For Amazon, compare AWS operating income and margin against North America and International from 2021 to 2025.',
  },
  {
    category: 'Growth drivers',
    prompt:
      'How did NVIDIA describe demand drivers, customer concentration, and supply constraints for Data Center from fiscal 2021 through 2025?',
  },
  {
    category: 'Language changes',
    prompt:
      "Across Microsoft's 2021–2025 filings, what changed in how it describes Azure, AI infrastructure, and cloud capacity constraints?",
  },
  {
    category: 'Geographic exposure',
    prompt:
      'Summarize the most important geographic revenue exposures disclosed in the latest 10-K for each company, and note year-over-year changes.',
  },
  {
    category: 'Risk factors',
    prompt:
      'Which companies materially changed risk-factor language on AI, export controls, or supply-chain concentration between 2021 and 2025?',
  },
]
