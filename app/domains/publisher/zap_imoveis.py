from app.domains.publisher import Publisher, Searcher, ModelMapper
from typing import Self
from playwright.async_api import Page, Locator, TimeoutError
from app.domains.browser import PageHelper, load_page
from app.domains import publications
from app.domains.models import PropertyPublication, PropertyType, ProposalType
import re
from enum import auto
import logging
from app.settings import PublisherSearchSettings
import rich
from datetime import datetime

logger = logging.getLogger(__name__)

property_type_mapper = dict(
    apartamento=PropertyType.APTO,
    casa=PropertyType.HOUSE,
    sobrados=PropertyType.TOWNHOUSES,
    casa_de_condominio=PropertyType.CONDO_HOUSE,
    others=PropertyType.OTHERS,
)

proposal_type_mapper = dict(
    venda=ProposalType.SELL,
    aluguel=ProposalType.RENT,
    others=auto(),
)


class BaseSearcher(Searcher):

    publisherSearchSettings: PublisherSearchSettings = (
        PublisherSearchSettings()
    )

    async def search(self, page: Page):
        base_search = self.publisherSearchSettings.base_search
        await page.get_by_text("Entendi").click()
        for location in base_search.locations:
            await page.get_by_label("Onde deseja morar?").fill(location)
            await page.get_by_label(location).check()

        await page.get_by_label("Tipo de imóvel").click()
        for property_type in base_search.property_types:
            await page.get_by_label(property_type, exact=True).check()
        await page.get_by_text("Buscar").click()


class BuySearcher(BaseSearcher):

    async def search(self, page: Page):
        buying_search = self.publisherSearchSettings.buying_search
        await page.get_by_role("tab", name="Comprar").click()

        await super().search(page)

        await page.wait_for_timeout(200)
        if await page.locator("div[aria-label='Fechar']").is_visible():
            await page.locator("div[aria-label='Fechar']").click()

        await page.get_by_role("button", name="Ordenar por").click()
        await page.get_by_text("Mais recente").click()

        await page.get_by_label("Máximo").first.fill(
            str(int(buying_search.maximum_price) or "")
        )
        await page.get_by_label("Máximo").nth(1).fill(
            str(int(buying_search.maximum_condominium_fee) or "")
        )
        await page.get_by_label("Mínimo").nth(2).fill(
            str(buying_search.minimum_square_meter or "")
        )
        await page.get_by_label("Máximo").nth(2).fill(
            str(buying_search.maximum_square_meter or "")
        )

        for num_bathrooms in buying_search.bathrooms:
            await page.get_by_role(
                "button", name=str(num_bathrooms)
            ).first.click()

        for num_bedrooms in buying_search.bedrooms:
            await page.get_by_role("button", name=str(num_bedrooms)).nth(
                1
            ).click()

        await page.get_by_text("Buscar Imóveis").click()


class RentSearcher(BaseSearcher):

    async def search(self, page: Page):
        renting_search = self.publisherSearchSettings.renting_search
        await page.get_by_role("tab", name="Alugar").click()

        await super().search(page)

        await page.wait_for_timeout(200)
        if await page.locator("div[aria-label='Fechar']").is_visible():
            await page.locator("div[aria-label='Fechar']").click()

        await page.get_by_role("button", name="Ordenar por").click()
        await page.get_by_text("Mais recente").click()

        await page.get_by_label("Máximo").first.fill(
            str(int(renting_search.maximum_price) or "")
        )
        await page.get_by_label("Mínimo").nth(1).fill(
            str(renting_search.minimum_square_meter or "")
        )
        await page.get_by_label("Máximo").nth(1).fill(
            str(renting_search.maximum_square_meter or "")
        )

        if renting_search.include_condominium_fee:
            await page.get_by_text("Incluir preço do condomínio").click()

        for num_bathrooms in renting_search.bathrooms:
            await page.get_by_role(
                "button", name=str(num_bathrooms)
            ).first.click()

        for num_bedrooms in renting_search.bedrooms:
            await page.get_by_role("button", name=str(num_bedrooms)).nth(
                1
            ).click()

        await page.get_by_text("Buscar Imóveis").click()


class ResultCardMapper(ModelMapper[Locator]):

    def __init__(self, locator: Locator) -> None:
        self._result_card = locator

    async def url(self) -> str:
        return await self._visible(self._result_card).get_attribute("href")

    async def address(self) -> str:
        all_text = (
            await self._visible(
                self._result_card.locator(".card__location > *")
            ).all_text_contents()
            or []
        )
        all_text.reverse()
        return ", ".join(filter(lambda text: len(text), all_text))

    async def details(self) -> str:
        return await self._visible(
            self._result_card.locator(".card__description")
        ).text_content()

    async def square_meter(self) -> int:
        match = re.match(
            r"\d*",
            await self._result_card.locator(
                "[itemprop=floorSize]"
            ).text_content()
            or "",
        ).group()
        return match and int(match)

    async def bedrooms(self) -> int:
        match = await self._visible(
            self._result_card.locator("[itemprop=numberOfRooms]")
        ).text_content()
        match = match and match.split(" - ")[-1]
        return match and int(match)

    async def bathrooms(self) -> int:
        match = await self._visible(
            self._result_card.locator("[itemprop=numberOfBathroomsTotal]")
        ).text_content()
        match = match and match.split(" - ")[-1]
        return match and int(match)

    async def car_spaces(self) -> int:
        match = await self._visible(
            self._result_card.locator("[itemprop=numberOfParkingSpaces]")
        ).text_content()
        match = match and match.split(" - ")[-1]
        return match and int(match)

    async def publisher(self) -> str:
        return ZapImoveis.name

    async def proposal(self) -> str:
        match = re.search(r"imovel/[a-z]+", await self.url())
        match = (
            match[0].replace(r"imovel/", "")
            if match
            else property_type_mapper.get("others")
        )
        return proposal_type_mapper.get(match) or proposal_type_mapper.get(
            "others"
        )

    async def type(self) -> str:
        match = re.search(r"imovel/[a-z]+-[a-z-]+-", await self.url())
        match = (
            re.sub(r"^imovel/[a-z]+-|-$", "", match[0])
            if match
            else property_type_mapper.get("others")
        )
        match = match.replace("-", "_")
        return property_type_mapper.get(match) or property_type_mapper.get(
            "others"
        )

    async def _prices(self) -> str:
        return await self._visible(
            self._result_card.locator(".listing-price")
        ).text_content()

    async def condominium_fee(self) -> float:
        match = re.search(r"Cond\. R\$ [0-9.]+", await self._prices())
        return (
            float(match[0].replace("Cond. R$ ", "").replace(".", ""))
            if match
            else None
        )

    async def iptu_tax(self) -> float:
        match = re.search(r"IPTU R\$ [0-9.]+", await self._prices())
        return (
            float(match[0].replace("IPTU R$ ", "").replace(".", ""))
            if match
            else None
        )

    async def rent_price(self) -> float:
        match = re.search(r"R\$ [0-9.]+", await self._prices())
        return (
            float(match[0].replace("R$ ", "").replace(".", ""))
            if match
            else None
        )

    async def printscreen(self) -> bytes:
        return await self._result_card.screenshot()


class PublicationMapper(ModelMapper[Locator]):

    def __init__(self, main_content: Locator) -> None:
        self._main_content = main_content

    async def _before(self):
        await self._main_content.locator(
            ".description__created-at"
        ).first.text_content()
        await self._visible(
            self._main_content.get_by_text("Todas as características")
        ).click()

    async def description(self) -> str:
        return await self._visible(
            self._main_content.locator(".description__title").first
        ).text_content()

    async def broker(self) -> str:
        return await self._visible(
            self._main_content.locator(
                ".desktop-only-container .advertiser-info__credentials--name"
            ).first
        ).text_content()

    async def buy_price(self) -> float:
        inner_Locator = self._main_content.locator(".price-both-wrapper")
        if await inner_Locator.is_hidden():
            inner_Locator = inner_Locator.or_(
                self._main_content.locator(".price-value-wrapper")
            )
        match = await self._visible(
            inner_Locator.locator("div", has_text="Venda")
            .locator(".price-info-value")
            .first
        ).text_content()
        match = re.search(r"[0-9.]+", match)
        return (
            float(match[0].replace("R$ ", "").replace(".", ""))
            if match
            else None
        )

    async def rent_price(self) -> float:
        inner_Locator = self._main_content.locator(".price-both-wrapper")
        if await inner_Locator.is_hidden():
            inner_Locator = inner_Locator.or_(
                self._main_content.locator(".price-value-wrapper")
            )
        match = await self._visible(
            inner_Locator.locator("div", has_text="Aluguel")
            .locator(".price-info-value")
            .first
        ).text_content()
        match = re.search(r"[0-9.]+", match)
        return (
            float(match[0].replace("R$ ", "").replace(".", ""))
            if match
            else None
        )

    async def floor(self) -> int:
        match = await self._visible(
            self._main_content.locator("[itemprop=floorLevel]")
        ).text_content()
        match = match and re.search(r"[0-9]+", match)
        return match and int(match[0])

    async def balcony(self) -> int:
        has_balcony = await self._visible(
            self._main_content.locator("[itemprop=balcony]")
        ).is_visible()
        return 1 if has_balcony else 0

    async def address(self) -> str:
        return await self._visible(
            self._main_content.locator(".address-info-value")
        ).text_content()

    async def publication_created_at(self) -> datetime:
        html_content = await self._main_content.page.content()
        match = re.search(
            r"createdAt.+:.+\d+-\d+-\d+T\d+:\d+:\d+", html_content
        )
        match = match and re.search(r"\d+-\d+-\d+T\d+:\d+:\d+", match[0])
        return datetime.strptime(match[0], "%Y-%m-%dT%H:%M:%S")

    async def publication_updated_at(self) -> datetime:
        html_content = await self._main_content.page.content()
        match = re.search(
            r"updatedAt.+:.+\d+-\d+-\d+T\d+:\d+:\d+", html_content
        )
        match = match and re.search(r"\d+-\d+-\d+T\d+:\d+:\d+", match[0])
        return datetime.strptime(match[0], "%Y-%m-%dT%H:%M:%S")


class ZapImoveis(Publisher):

    name: str = "Zap Imoveis"
    website: str = "https://www.zapimoveis.com.br/"
    searcherTypes: type[Searcher] = set(
        [
            BuySearcher,
            RentSearcher,
        ]
    )

    async def inspec(self, page: Page) -> Self:
        publication_count = []
        while True:
            await page.wait_for_timeout(1000 * 5)
            buttton_next_locator = page.locator(
                "section.listing-wrapper__pagination "
                "button[aria-label='Próxima página']"
            ).first

            logger.info("Scrolling down to the end of the page...")

            result_card_locator = page.locator("a.result-card")
            async for result_card in PageHelper.scroll_to_end(
                page,
                pixels_to_scroll=200,
                locator=result_card_locator,
                end=buttton_next_locator,
            ):
                result_card: Locator
                if await result_card.is_visible():
                    logger.info(
                        "Getting info from URL: %s",
                        await result_card.get_attribute("href"),
                    )
                await result_card.scroll_into_view_if_needed()
                publication = await ResultCardMapper(result_card).get_dict(
                    PropertyPublication
                )
                publications.save({**publication, "search_url": page.url})
                try:
                    async with page.context.expect_page() as new_page_info:
                        await result_card.click()
                    async with await new_page_info.value as new_page:
                        main_content = new_page.locator(
                            ".base-page__main-content"
                        )
                        detailed_publication = await PublicationMapper(
                            main_content
                        ).get_dict(PropertyPublication)
                        detailed_publication = {
                            "url": publication["url"],
                            **detailed_publication,
                        }
                        publications.save(detailed_publication)
                except TimeoutError:
                    raise

            publication_count.append(await result_card_locator.count())
            logger.info(
                "%s publication(s) found on page %s",
                publication_count[-1],
                len(publication_count),
            )

            if await buttton_next_locator.is_visible():
                logger.info("Going to next page...")
                await buttton_next_locator.scroll_into_view_if_needed()
                await buttton_next_locator.click()
            else:
                break
        logger.info("Total of %s publication(s) found", sum(publication_count))

    async def playground(self) -> Self:
        async with load_page(
            "https://www.zapimoveis.com.br/imovel/aluguel-apartamento-"
            "2-quartos-com-ar-condicionado-centro-sao-vicente-sp-52m2-"
            "id-2713416522/"
        ) as page:
            page: Page
            await page.wait_for_timeout(1000 * 1)
            main_content = page.locator(".base-page__main-content")
            publication = await PublicationMapper(main_content).get_dict(
                PropertyPublication
            )
            rich.print_json(data=publication, default=str)
            # await page.wait_for_timeout(60*1000)
