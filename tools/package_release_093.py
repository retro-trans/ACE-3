"""Package 0.9.3 with original-disc and published 0.9.0 upgrade routes."""
import package_release_047 as package

package.VERSION = '0.9.3'
package.MOVIE = package.DIR/'ACE3-English-0.9.3-orig-layout.iso'
package.OUTPUT = package.ROOT/'work/output/release-0.9.3'
package.TOOLS = package.ROOT/'work/local/retro-trans-release-065'
PREVIOUS = package.DIR/'ACE3-English-0.9.0-orig-layout.iso'
package.EXPECTED = {
    package.ORIGINAL: '5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705',
    PREVIOUS: '68b7fc22f7cde93b453223af0d45ca4e040be40f0edb263acc128f354e1e37d1',
}


def jobs():
    for version, source, name in [
        ('original', package.ORIGINAL, 'ACE3-English-0.9.3-movie.xdelta'),
        ('0.9.0', PREVIOUS, 'ACE3-English-0.9.0-to-0.9.3-movie.xdelta'),
    ]:
        yield dict(patch=name, edition='English prologue', language='en',
                   source_version=version, source_format='iso', target_format='iso',
                   source=str(source), target=str(package.MOVIE))


if __name__ == '__main__':
    package.jobs = jobs
    package.main()
