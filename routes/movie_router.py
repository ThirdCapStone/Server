from crawler.movie import MovieCrawler
from fastapi import APIRouter
import aiohttp
import asyncio

async def get_movie_list():
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=100000)) as session:
        movie_name_list = MovieCrawler.get_release_movie_name_list()
        tasks = [MovieCrawler.convert_movie_name_to_movie_code(session, movie_name) for movie_name in movie_name_list]
        result = set(await asyncio.gather(*tasks))
        result.discard(None)
        tasks = [MovieCrawler.get_movie_detail_from_movie_code(session, movie_code) for movie_code in result]
        result = await asyncio.gather(*tasks)
        return result

movie_list = asyncio.run(get_movie_list())

movie_router = APIRouter(
    prefix="/movie",
    tags=["movie"],
)

@movie_router.get("/")
async def get_movie_list():
    return list(map(lambda x: {key: x[key] for key in x.keys() & {"movie_code", "korean_movie_name", "english_movie_name", "main_poster", "movie_type", "movie_sort", "genres", "required_age", "release_date"}}, movie_list))


@movie_router.get("/{movie_code}")
async def get_movie_detail(movie_code: int):
    return list(filter(lambda x: x["movie_code"] == movie_code, movie_list))[0]

