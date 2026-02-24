# AI Applications Lab

This workshop empowers you to harness the transformative power of AI for tangible business outcomes. Gain a practical understanding of generative AI and its applications in areas like data analysis, content creation, and process automation.
Go beyond the hype and develop the skills to leverage AI for strategic decision-making, competitive advantage, and increased efficiency within your organization.

## Workshop Content

In this workshop, you will:
1. Understand the core concepts of how generative AI is revolutionizing industries.
2. Navigate leading AI platforms and identify the tools that align with your specific business needs.
3. Master prompt engineering techniques to effectively communicate with and direct AI models.
4. Go beyond text and leverage AI to analyze images, audio, and video for deeper insights.
5. Evaluate AI-generated content, identify trends, and extract knowledge to inform strategic decisions.

---

## 🚀 LinkedIn Marketing Agent

This repository now includes an intelligent LinkedIn Marketing Agent that:

- **Analyzes your business documents** (PDFs, Word docs) to understand your business
- **Generates compelling LinkedIn posts** using Claude AI (Anthropic)
- **Posts directly to LinkedIn** via API
- **Automates your daily marketing** with minimal effort

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure (copy .env.example to .env and add your keys)
cp .env.example .env

# Run in preview mode (no LinkedIn posting)
python run_agent.py --preview-only

# Generate and post to LinkedIn
python run_agent.py -n 1
```

📖 **[Read the full documentation →](LINKEDIN_AGENT_README.md)**

---
