# LinkedIn Marketing Agent 🚀

An intelligent agent that analyzes your business documents, generates compelling LinkedIn marketing campaigns using Claude AI, and posts them directly to your LinkedIn profile.

## 📋 Features

- **📚 Document Analysis**: Automatically reads and analyzes your business documents (PDFs, Word docs) to understand your business
- **🎨 AI-Powered Content Generation**: Uses Claude Opus 4.6 to create engaging, professional LinkedIn posts
- **📤 Direct LinkedIn Posting**: Publishes content directly to your LinkedIn profile via API
- **💾 Content Management**: Saves all generated posts for review and future reference
- **🔄 Daily Automation**: Designed for manual or scheduled daily execution

## 🏗️ Architecture

The agent consists of four main modules:

1. **Document Analyzer** (`document_analyzer.py`)
   - Extracts text from PDF and Word documents
   - Creates comprehensive business summaries

2. **Content Generator** (`content_generator.py`)
   - Analyzes business information using Claude
   - Generates engaging LinkedIn posts with strategic insights

3. **LinkedIn Poster** (`linkedin_poster.py`)
   - Handles LinkedIn API integration
   - Publishes posts to your LinkedIn profile

4. **Main Agent** (`agent.py`)
   - Orchestrates the complete workflow
   - Provides CLI interface and logging

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository (if not already done)
git clone <your-repo-url>
cd AI-applications-lab

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
# Required: Anthropic API Key
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Required for posting: LinkedIn credentials
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token_here
LINKEDIN_PERSON_URN=your_linkedin_person_urn_here

# Optional: Configuration
AGENT_MODEL=claude-opus-4-6
MAX_TOKENS=4096
DOCUMENTS_PATH=./
```

### 3. Get LinkedIn API Credentials

#### Option A: LinkedIn API (Official - Recommended for Organizations)

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Create an app
3. Request access to the "Share on LinkedIn" and "Sign In with LinkedIn" products
4. Generate an access token
5. Get your Person URN from LinkedIn API

**Note**: LinkedIn API access requires app approval and is primarily for organizations.

#### Option B: Preview-Only Mode (No LinkedIn Credentials Needed)

You can run the agent in preview-only mode to generate and review posts without LinkedIn credentials:

```bash
python run_agent.py --preview-only
```

### 4. Add Your Business Documents

Place your business documents (PDFs, Word docs) in the project directory. The agent will analyze:

- PDF files (`.pdf`)
- Word documents (`.doc`, `.docx`)

Examples of useful documents:
- Business presentations
- Proposals
- Marketing materials
- Company overviews
- Case studies

### 5. Run the Agent

#### Basic Usage (Preview Only)

```bash
python run_agent.py --preview-only
```

#### Generate Multiple Posts

```bash
python run_agent.py -n 5 --preview-only
```

#### Post to LinkedIn

```bash
python run_agent.py -n 1
```

## 📖 Usage Examples

### Generate and Preview 3 Posts

```bash
python run_agent.py -n 3 --preview-only
```

### Generate 1 Post and Post to LinkedIn

```bash
python run_agent.py -n 1
```

The agent will:
1. Analyze your business documents
2. Generate marketing content using Claude
3. Show you a preview
4. Ask for confirmation before posting
5. Post to LinkedIn
6. Save all posts to `generated_posts/` directory

### Preview Without Saving

```bash
python run_agent.py --preview-only --no-save
```

## 📂 Project Structure

```
AI-applications-lab/
├── linkedin_agent/
│   ├── __init__.py
│   ├── agent.py                 # Main orchestration
│   ├── config.py                # Configuration management
│   ├── document_analyzer.py     # Document processing
│   ├── content_generator.py     # Claude AI integration
│   └── linkedin_poster.py       # LinkedIn API integration
├── generated_posts/             # Saved posts (created automatically)
├── run_agent.py                 # Simple runner script
├── requirements.txt             # Python dependencies
├── .env                         # Your configuration (create this)
├── .env.example                 # Configuration template
└── LINKEDIN_AGENT_README.md     # This file
```

## 🔧 Advanced Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (required) | - |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn API access token | - |
| `LINKEDIN_PERSON_URN` | LinkedIn person URN | - |
| `AGENT_MODEL` | Claude model to use | `claude-opus-4-6` |
| `MAX_TOKENS` | Maximum tokens for generation | `4096` |
| `DOCUMENTS_PATH` | Path to business documents | `./` |
| `CONTENT_TONE` | Tone for generated content | `professional yet engaging` |
| `NUM_POSTS` | Default number of posts | `1` |

### Command Line Arguments

```bash
python run_agent.py --help
```

Options:
- `-n, --num-posts`: Number of posts to generate (default: 1)
- `-p, --preview-only`: Generate and preview without posting
- `--no-save`: Don't save posts to file

## 🤖 How It Works

### 1. Document Analysis Phase

The agent reads all PDF and Word documents in your project directory and extracts:
- Business focus and mission
- Key products/services
- Target audience
- Value propositions
- Areas of expertise

### 2. Content Generation Phase

Using Claude Opus 4.6 with adaptive thinking, the agent:
- Analyzes your business information
- Generates engaging LinkedIn posts
- Follows LinkedIn best practices
- Includes relevant hashtags and calls-to-action
- Provides strategic reasoning for each post

### 3. Publishing Phase

For each generated post, the agent:
- Shows you a preview
- Asks for confirmation
- Posts to LinkedIn via API
- Saves results for tracking

## 📅 Daily Automation

### Manual Execution

Run the agent daily:

```bash
# Generate today's post
python run_agent.py -n 1
```

### Scheduled Execution (Linux/Mac)

Add to crontab:

```bash
# Run every day at 9 AM
0 9 * * * cd /path/to/AI-applications-lab && /path/to/python run_agent.py -n 1
```

### Scheduled Execution (Windows)

Use Task Scheduler to run `run_agent.py` daily.

## 🔒 Security Best Practices

1. **Never commit `.env` file** - It contains your API keys
2. **Use environment variables** - Don't hardcode credentials
3. **Rotate access tokens** - Regularly update LinkedIn access tokens
4. **Review before posting** - Always preview posts before publishing
5. **Limit token permissions** - Use minimum required LinkedIn permissions

## 🐛 Troubleshooting

### "No documents found to analyze"

- Ensure PDF or Word documents are in the project directory
- Check `DOCUMENTS_PATH` in `.env`

### "LinkedIn credentials are invalid"

- Verify your `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_PERSON_URN`
- Check if your LinkedIn app has required permissions
- Access tokens may expire - regenerate if needed

### "ANTHROPIC_API_KEY is required"

- Create `.env` file from `.env.example`
- Add your Anthropic API key

### Posts not generating well

- Add more detailed business documents
- Adjust `CONTENT_TONE` in `.env`
- Try different prompts or focus areas

## 📝 Generated Post Format

Posts include:
- **Hook**: Attention-grabbing opening
- **Value**: Key insights or tips
- **Context**: Relevant to your business/expertise
- **Engagement**: Questions or calls-to-action
- **Hashtags**: 3-5 relevant hashtags
- **Length**: Optimized for LinkedIn (150-300 characters ideal)

## 🎯 Best Practices

1. **Update documents regularly** - Keep business materials current
2. **Review generated content** - Use preview mode first
3. **Maintain variety** - Generate multiple posts and choose the best
4. **Track performance** - Review saved posts to see what works
5. **Adjust tone** - Modify `CONTENT_TONE` based on your audience

## 🤝 Contributing

This is a personal project, but suggestions are welcome!

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/)
- Uses the LinkedIn API
- Inspired by modern AI-powered marketing automation

---

**Need help?** Check the troubleshooting section or review the example usage above.

**Ready to start?** Follow the Quick Start guide and generate your first post!
