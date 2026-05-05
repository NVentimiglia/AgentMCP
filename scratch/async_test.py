
import asyncio
async def main():
    print('OK')
    await asyncio.sleep(0.1)
    print('DONE')

if __name__ == "__main__":
    asyncio.run(main())
