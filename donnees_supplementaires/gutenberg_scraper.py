import os
import time
from playwright.sync_api import sync_playwright, TimeoutError

# Dossier où enregistrer les fichiers scrappés
DOWNLOAD_DIR = "livres_gutenberg"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Fonction de scrapping des textes du Projet Gutenberg de la catégorie French literature
def download_french_books():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        # URL de départ
        current_list_url = "https://www.gutenberg.org/ebooks/bookshelf/652?start_index=1001"

        while current_list_url:

            try:
                page.goto(current_list_url, timeout=60000)
                page.wait_for_load_state("networkidle")

                # Attendre jusqu'à 30 sec que les livres apparaissent
                page.wait_for_selector(
                    "li.booklink",
                    state="visible",
                    timeout=30000
                )

            except TimeoutError:
                print("Les livres ne sont jamais apparus.")
                break

            # On récupère tous les liens de livres sur la page 
            book_elements = page.query_selector_all("li.booklink a")

            urls_to_visit = []

            for link in book_elements:
                title = link.inner_text()
                href = link.get_attribute("href")
                
                # Vérifier que le texte est bien en français (certains de la catégorie French Literature sont en anglais)
                if "(French)" in title:
                    urls_to_visit.append(
                        f"https://www.gutenberg.org{href}"
                    )

            # Visiter chaque livre
            for book_url in urls_to_visit:
                try:
                    print(f"Visite du livre : {book_url}")

                    page.goto(book_url, timeout=60000)
                    page.wait_for_load_state("networkidle")

                    # Attendre que le lien du texte apparaisse
                    page.wait_for_selector(
                        "a[href*='.txt']",
                        timeout=15000
                    )

                    text_link_element = page.get_by_role(
                        "link",
                        name="Plain Text UTF-8"
                    )

                    if text_link_element.count() > 0:

                        download_url = text_link_element.get_attribute("href")

                        full_download_url = (
                            f"https://www.gutenberg.org{download_url}"
                        )

                        book_id = book_url.split('/')[-1]

                        path = os.path.join(
                            DOWNLOAD_DIR,
                            f"livre_{book_id}.txt"
                        )

                        # Téléchargement du texte
                        response = page.goto(full_download_url)

                        with open(path, "wb") as f:
                            f.write(response.body())

                        print(f"Sauvegardé : livre_{book_id}.txt")

                except TimeoutError:
                    print(f"Timeout sur {book_url}")

                except Exception as e:
                    print(f"Erreur sur {book_url}: {e}")

                # Retour à la page liste
                try:
                    page.goto(current_list_url, timeout=60000)
                    page.wait_for_load_state("networkidle")

                    page.wait_for_selector(
                        "li.booklink",
                        state="visible",
                        timeout=30000
                    )

                except TimeoutError:
                    print("Impossible de recharger la page liste.")
                    break

            # Chercher le bouton Next pour  passser à la page suivante
            next_link_selector = "//a[text()='Next']"

            next_link = page.locator(next_link_selector).first

            if next_link.is_visible():

                next_href = next_link.get_attribute("href")

                current_list_url = (
                    f"https://www.gutenberg.org{next_href}"
                )

            else:
                print("Plus de bouton Next. Fin du script.")
                current_list_url = None

        browser.close()

if __name__ == "__main__":
    download_french_books()