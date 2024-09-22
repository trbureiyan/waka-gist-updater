"""WakaBox: WakaTime progress visualizer for GitHub Gist.

This script fetches WakaTime stats and updates a GitHub Gist with the latest data.
"""

import os
import logging as logger
from base64 import b64encode
from datetime import datetime
from github import Github
from requests import get as rq_get
from requests.exceptions import RequestException

# Logger configuration
logger.basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    format="[%(asctime)s] ln. %(lineno)-3d %(levelname)-8s %(message)s",
    level=logger.DEBUG,
)

class WakaBox:
    def __init__(self):
        self.gh_token = os.getenv("GH_TOKEN")
        self.waka_key = os.getenv("WAKATIME_API_KEY")
        self.gist_id = os.getenv("GIST_ID")
        self.api_base_url = "https://wakatime.com/api/v1/users/current/stats"
        self.time_range = "last_7_days"
        
        # Validate inputs
        if not all([self.gh_token, self.waka_key, self.gist_id]):
            logger.error("Environment variables GH_TOKEN, WAKATIME_API_KEY, and GIST_ID must be set.")
            raise ValueError("Missing required environment variables.")

    def fetch_stats(self):
        """Fetch WakaTime stats."""
        encoded_key = b64encode(self.waka_key.encode()).decode()
        try:
            response = rq_get(f"{self.api_base_url}/{self.time_range}", headers={"Authorization": f"Basic {encoded_key}"})
            response.raise_for_status()  # Verify if the response was successful
            return response.json().get("data")
        except RequestException as e:
            logger.error(f"Failed to fetch stats: {e}")
            raise
        """response = rq_get(
            f"{self.api_base_url}/{self.time_range}",
            headers={"Authorization": f"Basic {encoded_key}"},
        )
        if response.status_code != 200:
            logger.error(f"Failed to fetch stats: {response.status_code} - {response.text}")
            raise RequestException("Failed to fetch WakaTime stats.")
        return response.json().get("data")
        """

    def make_title(self, start, end):
        """Create title for the stats."""
        msg_dfm = "%d %B %Y"
        start_date = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ").strftime(msg_dfm)
        end_date = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ").strftime(msg_dfm)
        return f"From: {start_date} - To: {end_date}"

    def make_graph(self, percent, length):
        """Generate a graphical representation of the percentage."""
        block = "█"
        empty = "░"
        filled_length = int(length * percent // 100)
        return block * filled_length + empty * (length - filled_length)

    def prepare_content(self, stats):
        """Prepare markdown content from the fetched statistics."""
        logger.debug("Preparing content for Gist update.")
        content = self.make_title(stats["start"], stats["end"]) + "\n\n"
        total_time = stats.get("human_readable_total")
        content += f"Total Time: {total_time}\n\n"

        for lang in stats.get("languages", [])[:5]:  # Limit to top 5 languages
            name = lang["name"]
            time = lang["text"]
            percent = lang["percent"]
            graph = self.make_graph(percent, 20)
            content += f"{name.ljust(10)} {time.ljust(14)} {graph} {percent:.2f}%\n"

        return content.strip()

    def update_gist(self, content):
        """Update the GitHub Gist with the new content."""
        try:
            gh = Github(self.gh_token)
            gist = gh.get_gist(self.gist_id)
            filename = list(gist.files.keys())[0]
            gist.edit(files={filename: {"content": content}})
            logger.info("Gist updated successfully!")
        except Exception as e:
            logger.error(f"Failed to update Gist: {e}")
        
        """
        gh = Github(self.gh_token)
        gist = gh.get_gist(self.gist_id)
        filename = list(gist.files.keys())[0]
        gist.edit(files={filename: {"content": content}})
        logger.info("Gist updated successfully!")
        """

    def run(self):
        """Main execution method."""
        try:
            logger.debug("Fetching WakaTime statistics.")
            stats = self.fetch_stats()
            logger.debug("Preparing content for Gist.")
            content = self.prepare_content(stats)
            logger.debug("Updating Gist with new content.")
            self.update_gist(content)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            
        """
        logger.debug("Fetching WakaTime statistics.")
        stats = self.fetch_stats()
        logger.debug("Preparing content for Gist.")
        content = self.prepare_content(stats)
        logger.debug("Updating Gist with new content.")
        self.update_gist(content)
        """

if __name__ == "__main__":
    try:
        waka_box = WakaBox()
        waka_box.run()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
