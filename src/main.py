from parser.strategies.stupino_flat_links import AvitoFlatLinksCollector
from config.settings import settings


def main():
    collector = AvitoFlatLinksCollector(
        base_url=settings.target_url,
    )

    links = collector.collect_all_links()
    collector.save_links_to_file()

    return len(links)


if __name__ == "__main__":
    main()
