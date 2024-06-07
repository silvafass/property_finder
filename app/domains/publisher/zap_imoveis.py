from app.domains.publisher import Publisher, Searcher, ModelMapper
from typing import Self
from playwright.async_api import Page, Locator
from app.domains.browser import PageHelper
from app.domains import publications
from app.domains.models import PropertyPublication, PropertyType, ProposalType
import re
from enum import auto
import logging
from app.settings import PublisherSearchSettings

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

    async def price(self) -> float:
        match = re.search(r"R\$ [0-9.]+", await self._prices())
        return (
            float(match[0].replace("R$ ", "").replace(".", ""))
            if match
            else None
        )

    async def printscreen(self) -> bytes:
        return await self._result_card.screenshot()


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
                await result_card.scroll_into_view_if_needed()
                publication = await ResultCardMapper(result_card).get_dict(
                    PropertyPublication
                )
                publications.save(publication)

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
