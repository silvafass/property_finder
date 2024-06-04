from app.domains.publisher import Publisher, Searcher, ModelMapper
from typing import Self
from playwright.async_api import Page, Locator
from app.domains.browser import PageHelper
from app.domains import publications
from app.domains.models import PropertyPublication, PropertyType, ProposalType
import re
from enum import auto
import logging

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

    async def search(self, page: Page):
        await page.get_by_text("Entendi").click()
        for location in [
            "Vila Cascatinha, São Vicente - SP",
            "Vila Valença, São Vicente - SP",
            "Boa Vista, São Vicente - SP",
            "Pompeia, Santos - SP",
            "Campo Grande, Santos - SP",
            "Embaré, Santos - SP",
        ]:
            await page.get_by_label("Onde deseja morar?").fill(location)
            await page.get_by_label(location).check()

        await page.get_by_label("Tipo de imóvel").click()
        for property_type in [
            "Apartamento",
            "Casa",
            "Sobrado",
            "Casa de Condomínio",
        ]:
            await page.get_by_label(property_type, exact=True).check()
        await page.get_by_text("Buscar").click()


class BuySearcher(BaseSearcher):

    async def search(self, page: Page):
        await page.get_by_role("tab", name="Comprar").click()

        await super().search(page)

        await page.get_by_role("button", name="Ordenar por").click()
        await page.get_by_text("Mais recente").click()

        await page.get_by_label("Máximo").first.fill("400000")
        await page.get_by_label("Máximo").nth(1).fill("500")
        await page.get_by_label("Máximo").nth(2).fill("75")

        # # Bathroom
        # await page.get_by_role("button", name="2").first.click()
        # await page.get_by_role("button", name="3").first.click()

        await page.get_by_role("button", name="2").nth(1).click()
        await page.get_by_role("button", name="3").nth(1).click()

        await page.get_by_text("Buscar Imóveis").click()


class RentSearcher(BaseSearcher):

    async def search(self, page: Page):
        await page.get_by_role("tab", name="Alugar").click()

        await super().search(page)

        await page.get_by_role("button", name="Ordenar por").click()
        await page.get_by_text("Mais recente").click()

        await page.get_by_label("Máximo").first.fill("2600")
        await page.get_by_label("Máximo").nth(1).fill("75")

        await page.get_by_text("Incluir preço do condomínio").click()

        # # Bathroom
        # await page.get_by_role("button", name="2").first.click()
        # await page.get_by_role("button", name="3").first.click()

        await page.get_by_role("button", name="2").nth(1).click()
        await page.get_by_role("button", name="3").nth(1).click()

        await page.get_by_text("Buscar Imóveis").click()


class ResultCardMapper(ModelMapper):

    def __init__(self, locator: Locator) -> None:
        self._result_card = locator

    async def url(self):
        return await self._result_card.get_attribute("href")

    async def publisher(self) -> str:
        return ZapImoveis.name

    async def proposal(self) -> str:
        match = re.search(r"imovel/[a-z]+", await self.url())
        match = (
            match[0].replace(r"imovel/", "")
            if match
            else property_type_mapper.others
        )
        return proposal_type_mapper.get(match) or proposal_type_mapper.others

    async def type(self) -> str:
        match = re.search(r"imovel/[a-z]+-[a-z-]+-", await self.url())
        match = (
            re.sub(r"^imovel/[a-z]+-|-$", "", match[0])
            if match
            else property_type_mapper.others
        )
        match = match.replace("-", "_")
        return property_type_mapper.get(match) or property_type_mapper.others

    async def _prices(self) -> str:
        return await self._result_card.locator(".listing-price").text_content()

    async def maintenance_fee_value(self) -> float:
        match = re.search(r"Cond\. R\$ [0-9.]+", await self._prices())
        return (
            float(match[0].replace("Cond. R$ ", "").replace(".", ""))
            if match
            else None
        )

    async def iptu_value(self) -> float:
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

            logger.info("Scrolling down to the end of the page...")
            await PageHelper.scroll_to_end(page, pixels_to_scroll=400)

            result_card_locator = page.locator("a.result-card")
            publication_count.append(await result_card_locator.count())
            logger.info(
                "%s publication(s) found on page %s",
                publication_count[-1],
                len(publication_count),
            )

            for result_card in await result_card_locator.all():
                await result_card.scroll_into_view_if_needed()
                publication = await ResultCardMapper(result_card).get_dict(
                    PropertyPublication
                )
                publications.save(publication)

            buttton_next_locator = page.locator(
                "section.listing-wrapper__pagination "
                "button[aria-label='Próxima página']"
            ).first
            if await buttton_next_locator.is_visible():
                logger.info("Going to next page...")
                await buttton_next_locator.scroll_into_view_if_needed()
                await buttton_next_locator.click()
            else:
                break
        logger.info("Total of %s publication(s) found", sum(publication_count))
