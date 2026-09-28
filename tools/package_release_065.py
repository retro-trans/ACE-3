"""Package build 0.1.64 as release 0.1.65 with verified original/0.1.47 routes.

Run relayout_disc.py ACE3-English-0.1.64.iso first. The release identity differs
from the local test disc because release mastering changes its byte layout.
The current upstream validator must be checked out under the ignored path below.
"""
import package_release_047 as package

package.VERSION = '0.1.65'
package.MOVIE = package.DIR/'ACE3-English-0.1.64-orig-layout.iso'
package.OUTPUT = package.ROOT/'work/output/release-0.1.65'
package.TOOLS = package.ROOT/'work/local/retro-trans-release-065'
PREVIOUS = package.DIR/'ACE3-English-0.1.47-orig-layout.iso'
package.EXPECTED = {
    package.ORIGINAL: '5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705',
    PREVIOUS: 'b86f9a52d2b8bfae419d5a7d7bd48d59665787b3e6393e3722d9dc757129aa8e',
}


def jobs():
    for version, source, name in [
        ('original', package.ORIGINAL, 'ACE3-English-0.1.65-movie.xdelta'),
        ('0.1.47', PREVIOUS, 'ACE3-English-0.1.47-to-0.1.65-movie.xdelta'),
    ]:
        yield dict(patch=name,edition='English prologue',language='en',
                   source_version=version,source_format='iso',target_format='iso',
                   source=str(source),target=str(package.MOVIE))


if __name__=='__main__':
    package.jobs=jobs
    package.main()
