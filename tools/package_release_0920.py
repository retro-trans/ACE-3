"""Package 0.9.20 with original-disc and published 0.9.16 upgrade routes.

Use Python 3.12+. First run relayout_disc.py ACE3-English-0.9.20.iso.
The upstream release standard and validator are pinned to the reviewed commit.
"""
import package_release_047 as package

package.VERSION = '0.9.20'
package.MOVIE = package.DIR/'ACE3-English-0.9.20-orig-layout.iso'
package.OUTPUT = package.ROOT/'work/output/release-0.9.20'
package.TOOLS = package.ROOT/'work/local/retro-trans-release-0920/retro-trans-tools-34713d556592677891c5dc55c0e30e7b38df1923'
PREVIOUS = package.DIR/'ACE3-English-0.9.16-orig-layout.iso'
package.EXPECTED = {
    package.ORIGINAL: '5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705',
    PREVIOUS: 'fc6112fd08e897dd050426ffb89e1dd4d5c23de79d894642c0b2f9712ec06b22',
}


def jobs():
    for version, source, name in [
        ('original', package.ORIGINAL, 'ACE3-English-0.9.20-movie.xdelta'),
        ('0.9.16', PREVIOUS, 'ACE3-English-0.9.16-to-0.9.20-movie.xdelta'),
    ]:
        yield dict(patch=name, edition='English prologue', language='en',
                   source_version=version, source_format='iso', target_format='iso',
                   source=str(source), target=str(package.MOVIE))


if __name__ == '__main__':
    package.jobs = jobs
    package.main()
