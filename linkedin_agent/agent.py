"""Main LinkedIn Marketing Agent script."""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import colorama
from colorama import Fore, Style

from .config import AgentConfig
from .document_analyzer import DocumentAnalyzer
from .content_generator import ContentGenerator
from .linkedin_poster import LinkedInPoster


colorama.init(autoreset=True)


class LinkedInMarketingAgent:
    """LinkedIn Marketing Agent - Analyzes business, generates campaigns, and posts to LinkedIn."""

    def __init__(self, config: AgentConfig):
        """Initialize the LinkedIn Marketing Agent.

        Args:
            config: Agent configuration
        """
        self.config = config
        self.document_analyzer = DocumentAnalyzer(config.documents_path)
        self.content_generator = ContentGenerator(
            api_key=config.anthropic_api_key,
            model=config.model,
            max_tokens=config.max_tokens
        )
        self.linkedin_poster = None

        if config.linkedin_access_token and config.linkedin_person_urn:
            self.linkedin_poster = LinkedInPoster(
                access_token=config.linkedin_access_token,
                person_urn=config.linkedin_person_urn
            )

    def run(
        self,
        num_posts: int = 1,
        preview_only: bool = False,
        save_to_file: bool = True
    ) -> List[Dict]:
        """Run the complete marketing agent workflow.

        Args:
            num_posts: Number of posts to generate
            preview_only: If True, only generate and preview posts without posting
            save_to_file: If True, save generated posts to a JSON file

        Returns:
            List of generated posts with metadata
        """
        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.CYAN}  LinkedIn Marketing Agent")
        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

        # Step 1: Analyze documents
        print(f"{Fore.YELLOW}📚 Step 1: Analyzing Business Documents{Style.RESET_ALL}")
        print("-" * 70)
        analyzed_docs = self.document_analyzer.analyze_documents()

        if not analyzed_docs:
            print(f"{Fore.RED}✗ No documents found to analyze!")
            print(f"{Fore.YELLOW}  Please add PDF or Word documents to {self.config.documents_path}{Style.RESET_ALL}")
            sys.exit(1)

        business_summary = self.document_analyzer.create_business_summary(analyzed_docs)
        print(f"\n{Fore.GREEN}✓ Analyzed {len(analyzed_docs)} document(s){Style.RESET_ALL}\n")

        # Step 2: Generate marketing content
        print(f"{Fore.YELLOW}🎨 Step 2: Generating Marketing Content{Style.RESET_ALL}")
        print("-" * 70)
        posts = self.content_generator.generate_campaign(
            business_docs_summary=business_summary,
            num_posts=num_posts,
            tone=self.config.tone
        )
        print(f"\n{Fore.GREEN}✓ Generated {len(posts)} post(s){Style.RESET_ALL}\n")

        # Step 3: Preview posts
        print(f"{Fore.YELLOW}👀 Step 3: Previewing Generated Content{Style.RESET_ALL}")
        print("-" * 70)
        for i, post in enumerate(posts, 1):
            self._preview_post(post, i)

        # Save to file if requested
        if save_to_file:
            self._save_posts_to_file(posts)

        # Step 4: Post to LinkedIn (if not preview-only)
        if not preview_only:
            if not self.linkedin_poster:
                print(f"\n{Fore.RED}✗ LinkedIn credentials not configured!")
                print(f"{Fore.YELLOW}  Add LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN to .env file{Style.RESET_ALL}")
                print(f"{Fore.CYAN}  Running in preview-only mode.{Style.RESET_ALL}")
                return posts

            print(f"\n{Fore.YELLOW}📤 Step 4: Posting to LinkedIn{Style.RESET_ALL}")
            print("-" * 70)

            # Validate credentials first
            if not self.linkedin_poster.validate_credentials():
                print(f"{Fore.RED}✗ LinkedIn credentials are invalid!")
                print(f"{Fore.YELLOW}  Posts have been saved but not published.{Style.RESET_ALL}")
                return posts

            # Post each generated post
            for i, post in enumerate(posts, 1):
                print(f"\n{Fore.CYAN}Posting {i}/{len(posts)}...{Style.RESET_ALL}")
                user_input = input(f"Post this to LinkedIn? (y/n/skip all): ").lower()

                if user_input == 'skip all':
                    print(f"{Fore.YELLOW}Skipping remaining posts...{Style.RESET_ALL}")
                    break
                elif user_input != 'y':
                    print(f"{Fore.YELLOW}Skipped post {i}{Style.RESET_ALL}")
                    post['posted'] = False
                    continue

                result = self.linkedin_poster.create_post(post['post'])
                post['linkedin_result'] = result
                post['posted'] = result.get('success', False)

                if result.get('success'):
                    print(f"{Fore.GREEN}✓ Post {i} published successfully!{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}✗ Failed to post {i}{Style.RESET_ALL}")

            # Save updated posts with posting results
            if save_to_file:
                self._save_posts_to_file(posts, suffix="_with_results")

        else:
            print(f"\n{Fore.CYAN}ℹ️  Preview-only mode: Posts were not published to LinkedIn{Style.RESET_ALL}")

        print(f"\n{Fore.GREEN}{'=' * 70}")
        print(f"{Fore.GREEN}  ✓ LinkedIn Marketing Agent Complete!")
        print(f"{Fore.GREEN}{'=' * 70}{Style.RESET_ALL}\n")

        return posts

    def _preview_post(self, post: dict, number: int):
        """Preview a generated post.

        Args:
            post: Post data
            number: Post number
        """
        print(f"\n{Fore.CYAN}┌─ Post {number} ─────────────────────────────────────────────────────┐{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{post['post']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}└───────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
        print(f"\n{Fore.MAGENTA}Strategy: {post['reasoning'][:150]}...{Style.RESET_ALL}\n")

    def _save_posts_to_file(self, posts: List[Dict], suffix: str = ""):
        """Save generated posts to a JSON file.

        Args:
            posts: List of generated posts
            suffix: Optional suffix for filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"linkedin_posts_{timestamp}{suffix}.json"

        output_dir = Path("generated_posts")
        output_dir.mkdir(exist_ok=True)

        filepath = output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(posts, f, indent=2)

        print(f"\n{Fore.GREEN}✓ Posts saved to: {filepath}{Style.RESET_ALL}")


def main():
    """Main entry point for the LinkedIn Marketing Agent."""
    import argparse

    parser = argparse.ArgumentParser(
        description="LinkedIn Marketing Agent - Automated business analysis and content generation"
    )
    parser.add_argument(
        "-n", "--num-posts",
        type=int,
        default=1,
        help="Number of posts to generate (default: 1)"
    )
    parser.add_argument(
        "-p", "--preview-only",
        action="store_true",
        help="Generate and preview posts without posting to LinkedIn"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save posts to file"
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config = AgentConfig.from_env()

        # Create and run agent
        agent = LinkedInMarketingAgent(config)
        agent.run(
            num_posts=args.num_posts,
            preview_only=args.preview_only,
            save_to_file=not args.no_save
        )

    except Exception as e:
        print(f"\n{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
